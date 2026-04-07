import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float64MultiArray
from hre_interfaces.msg import Imu as ImuMsg
from hre_interfaces.msg import Smg as SmgMsg
from hre_interfaces.msg import Emg as EmgMsg
import numpy as np


class StretchSimControlNode(Node):
    def __init__(self):
        super().__init__('stretch_sim_control')

        self.declare_parameter('emg_topic', 'processed/emg')
        self.declare_parameter('output_emg', 'stretch_sim/emg')

        self.declare_parameter('imu_topic', 'processed/imu')
        self.declare_parameter('output_imu', 'stretch_sim/imu')
        
        self.declare_parameter('smg_topic', 'processed/smg')
        self.declare_parameter('output_smg', 'stretch_sim/smg')

        # Threshold for EMG "active" detection
        self.declare_parameter('emg_threshold', 0.8)

        # Refractory period (per EMG channel)
        self.declare_parameter('emg_refractory_sec', 1.0)

        # Per-channel refractory state: next time (ns) a channel is allowed to output True again
        self._next_allowed_ns = []

        imu_topic = self.get_parameter('imu_topic').value
        output_imu = self.get_parameter('output_imu').value
        self.pub_imu = self.create_publisher(Float64MultiArray, output_imu, 10)

        emg_topic = self.get_parameter('emg_topic').value
        output_emg = self.get_parameter('output_emg').value
        self.pub_emg = self.create_publisher(Int32MultiArray, output_emg, 10)

        smg_topic = self.get_parameter('smg_topic').value
        output_smg = self.get_parameter('output_smg').value
        self.pub_smg = self.create_publisher(Float64MultiArray, output_smg, 10)

        self.latest_smg = None

        self.sub_smg = self.create_subscription(
            SmgMsg, smg_topic, self.smg_cb, 10
        )
        self.sub_emg = self.create_subscription(
            EmgMsg, emg_topic, self.emg_cb, 10
        )
        self.sub_imu = self.create_subscription(
            ImuMsg, imu_topic, self.imu_cb, 10
        )

        self.acc_max = [0,0,0]
        self.acc_min = [0,0,0]

        self.command_prev = 0
        self.alpha = 0.1
        self.mean = [-0.14095349, 0.52626293, 0.6630938,  -8.09277865, -6.63937388, -4.06168228]
        self.std = [ 0.20067332,  0.38428758,  0.18261657, 68.47851077, 40.54749376, 55.34736842]
        self.v2 = [-0.60007158,-0.13430892,0.24827067,-0.0860092, -0.560094977, -0.48906396]

    # ---------------------------- PCA to COMMAND FUNC ----------------------------
    def PCA_2_command(self, acc):  
        # Turning this into np arrays so python can do the math easier.
        data = np.array(acc)

        # Pull out values
        v2_crop = np.array(self.v2[0:3])
        mean_crop = np.array(self.mean[0:3])
        std_crop = np.array(self.std[0:3])
        
        # Find and use data center
        data_cent = (data-mean_crop)/std_crop
        command = np.dot(v2_crop, data_cent)

        # Low pass filter for jitter
        command = (self.alpha*command) + (1-self.alpha)*self.command_prev
        self.command_prev = command

        return command
    # -----------------------------------------------------------------------------
    
    # ---------------------------- MAP to COMMAND FUNC ----------------------------
    def map_data(self, acc):
        imu_min = -0.33
        imu_max = 0.35

        print("Hello")

        command = (acc[1]-self.acc_max[1])/(self.acc_max[1]-self.acc_min[1])

        if self.command_prev is None:
            self.command_prev = command

        command = (self.alpha*acc[1]) + (1-self.alpha)*self.command_prev
        self.command_prev = command

        return command
    # -----------------------------------------------------------------------------

    # ---------------------------- IMU to COMMAND HERE ----------------------------
    def imu_cb(self, msg: ImuMsg):
        # Setup
        out = Float64MultiArray()
        acc = [msg.acc_x[0], msg.acc_y[0], msg.acc_z[0]]
        gyro = [msg.gyro_x[0], msg.gyro_y[0], msg.gyro_z[0]]
        name = msg.sensor_name[0]

        # Save new min and max if necessary (for each DOF (x,y,z))
        for i in range(3):
            if acc[i] < self.acc_min[i]: self.acc_min[i] = acc[i]
            if acc[i] > self.acc_max[i]: self.acc_max[i] = acc[i]

        command = self.map_data(acc)
        out.data.append(command)
        
        # Publish Command
        self.pub_smg.publish(out)
        # self.pub_imu.publish(out)
    # -----------------------------------------------------------------------------

    def smg_cb(self, msg: SmgMsg):
        out = Float64MultiArray()
        out.data = msg.smg
        # self.pub_smg.publish(out)

    def emg_cb(self, msg: EmgMsg):
        thr = float(self.get_parameter('emg_threshold').value)

        # Combining sensors into one list
        nSens = len(msg.sensor_name)
        data = []
        for i in range(nSens):
            data.extend([msg.emg1[i], msg.emg2[i], msg.emg3[i], msg.emg4[i]])

        # Threshold EMG channels
        active_channels = [float(x) >= thr for x in data]

        # --- Refractory gating (per channel) ---
        refractory_sec = float(self.get_parameter('emg_refractory_sec').value)
        refractory_ns = int(refractory_sec * 1e9)
        now_ns = int(self.get_clock().now().nanoseconds)

        # Ensure state matches channel count
        n_ch = len(data)
        if len(self._next_allowed_ns) != n_ch:
            self._next_allowed_ns = [0] * n_ch

        gated_channels = [False] * n_ch
        for i, is_active in enumerate(active_channels):
            if now_ns < self._next_allowed_ns[i]:
                gated_channels[i] = False
                continue

            if is_active:
                gated_channels[i] = True
                self._next_allowed_ns[i] = now_ns + refractory_ns
            else:
                gated_channels[i] = False

        out = Int32MultiArray()
        out.data = [int(x) for x in gated_channels]
        # self.pub_emg.publish(out)


def main():
    rclpy.init()
    node = StretchSimControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float64MultiArray, Bool
from stretch_sim_interfaces.msg import DelsysMsg, EmgMsg, SmgMsg, ImuMsg


class StretchSimControlNode(Node):
    def __init__(self):
        super().__init__('stretch_sim_control')

        self.declare_parameter('delsys_topic', 'processed/emg')
        self.declare_parameter('output_emg', 'stretch_sim/emg')
        
        self.declare_parameter('telemed_topic', 'processed/smg')
        self.declare_parameter('output_smg', 'stretch_sim/smg')

        # Threshold for EMG "active" detection
        self.declare_parameter('emg_threshold', 0.8)

        # NEW: EMG channel handling
        self.declare_parameter('emg_mode', 'first')      # 'first', 'any', 'all'

        # Refractory period (per EMG channel)
        self.declare_parameter('emg_refractory_sec', 1.0)

        # Per-channel refractory state: next time (ns) a channel is allowed to output True again
        self._next_allowed_ns = []

        delsys_topic = self.get_parameter('delsys_topic').value
        telemed_topic = self.get_parameter('telemed_topic').value
        output_smg = self.get_parameter('output_smg').value
        output_emg = self.get_parameter('output_emg').value

        self.pub_smg = self.create_publisher(Float64MultiArray, output_smg, 10)
        self.pub_emg = self.create_publisher(Bool, output_emg, 10)

        self.latest_smg = None

        self.sub_telemed = self.create_subscription(
            SmgMsg, telemed_topic, self.telemed_cb, 10
        )
        self.sub_delsys = self.create_subscription(
            EmgMsg, delsys_topic, self.delsys_cb, 10
        )

        self.get_logger().info(f"Subscribing telemed (SMG passthrough): {telemed_topic}")
        self.get_logger().info(f"Subscribing delsys  (EMG threshold):   {delsys_topic}")
        self.get_logger().info(f"Publishing stretch_sim (SMG):          {output_smg}")
        self.get_logger().info(f"Publishing stretch_sim (EMG):          {output_emg}")

    def telemed_cb(self, msg: SmgMsg):
        out = Float64MultiArray()
        out.data = [float(x) for x in msg.data]
        self.pub_smg.publish(out)

    def delsys_cb(self, msg: EmgMsg):
        thr = float(self.get_parameter('emg_threshold').value)
        mode = self.get_parameter('emg_mode').value

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
        # --------------------------------------

        # Combine channels → single bool
        if mode == 'first':
            emg_active = gated_channels[0]
        elif mode == 'all':
            emg_active = all(gated_channels)
        else:  # 'any' (default)
            emg_active = any(gated_channels)

        out = Bool()
        out.data = bool(emg_active)
        self.pub_emg.publish(out)


def main():
    rclpy.init()
    node = StretchSimControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
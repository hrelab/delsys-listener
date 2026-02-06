import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from stretch_sim_interfaces.msg import StretchSimSignals


class StretchSimControlNode(Node):
    def __init__(self):
        super().__init__('stretch_sim_control')

        self.declare_parameter('delsys_topic', '/delsys_data/processed')
        self.declare_parameter('telemed_topic', '/telemed_data/processed')
        self.declare_parameter('output_topic', '/stretch_sim/signals')

        # Threshold for EMG "active" detection
        self.declare_parameter('emg_threshold', 0.05)

        delsys_topic = self.get_parameter('delsys_topic').value
        telemed_topic = self.get_parameter('telemed_topic').value
        output_topic = self.get_parameter('output_topic').value

        self.pub = self.create_publisher(StretchSimSignals, output_topic, 10)

        self.latest_smg = None

        self.sub_telemed = self.create_subscription(
            Float32MultiArray, telemed_topic, self.telemed_cb, 10
        )
        self.sub_delsys = self.create_subscription(
            Float32MultiArray, delsys_topic, self.delsys_cb, 10
        )

        self.get_logger().info(f"Subscribing telemed (SMG passthrough): {telemed_topic}")
        self.get_logger().info(f"Subscribing delsys  (EMG threshold):   {delsys_topic}")
        self.get_logger().info(f"Publishing StretchSimSignals:          {output_topic}")

    def telemed_cb(self, msg: Float32MultiArray):
        # Pass-through: store as float64 list for the outgoing message
        self.latest_smg = [float(x) for x in msg.data]

    def delsys_cb(self, msg: Float32MultiArray):
        # If we haven't received telemed yet, either publish empty smg or skip.
        # Here: publish empty smg until telemed arrives.
        smg = self.latest_smg if self.latest_smg is not None else []

        thr = float(self.get_parameter('emg_threshold').value)

        # msg.data already rectified+RMS (from delsys_listener), so just threshold it
        emg_active = [bool(float(x) >= thr) for x in msg.data]

        out = StretchSimSignals()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = ""
        out.smg = smg
        out.emg_active = emg_active

        self.pub.publish(out)


def main():
    rclpy.init()
    node = StretchSimControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
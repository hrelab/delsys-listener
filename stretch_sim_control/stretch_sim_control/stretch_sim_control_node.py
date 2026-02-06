import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from message_filters import Subscriber, ApproximateTimeSynchronizer

from stretch_sim_interfaces.msg import StretchSimSignals


class StretchSimControlNode(Node):
    def __init__(self):
        super().__init__('stretch_sim_control')

        self.declare_parameter('delsys_topic', '/delsys-data/processed')
        self.declare_parameter('telemed_topic', '/telemed-data/processed')
        self.declare_parameter('output_topic', '/stretch_sim/signals')

        delsys_topic = self.get_parameter('delsys_topic').get_parameter_value().string_value
        telemed_topic = self.get_parameter('telemed_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        # Publisher for custom message
        self.pub = self.create_publisher(StretchSimSignals, output_topic, 10)

        # message_filters subscribers
        self.sub_delsys = Subscriber(self, Float32MultiArray, delsys_topic)
        self.sub_telemed = Subscriber(self, Float32MultiArray, telemed_topic)

        # Approximate sync since these streams usually won't be perfectly aligned
        self.sync = ApproximateTimeSynchronizer(
            [self.sub_delsys, self.sub_telemed],
            queue_size=20,
            slop=0.02,  # seconds; tune as needed
            allow_headerless=True
        )
        self.sync.registerCallback(self.synced_cb)

        self.get_logger().info(f"Subscribing delsys:  {delsys_topic}")
        self.get_logger().info(f"Subscribing telemed: {telemed_topic}")
        self.get_logger().info(f"Publishing:         {output_topic}")

    def process_signals(self, delsys_vals, telemed_vals):
        """
        Replace this with whatever processing you want.
        Return:
          smg_float64_list, emg_int_list
        """
        # EXAMPLE PLACEHOLDER:
        # - smg: concatenate both streams as float64
        smg = [float(x) for x in (delsys_vals + telemed_vals)]

        # - emg: convert delsys stream into ints (toy example)
        #   (You will almost certainly change this logic.)
        emg = [int(round(abs(x) * 1000.0)) for x in delsys_vals]

        return smg, emg

    def synced_cb(self, delsys_msg: Float32MultiArray, telemed_msg: Float32MultiArray):
        delsys_vals = list(delsys_msg.data)
        telemed_vals = list(telemed_msg.data)

        smg, emg = self.process_signals(delsys_vals, telemed_vals)

        out = StretchSimSignals()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = ""  # set if you want
        out.smg = smg
        out.emg = emg

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
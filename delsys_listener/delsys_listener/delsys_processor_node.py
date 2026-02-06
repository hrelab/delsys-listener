import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class DelsysProcessor(Node):
    def __init__(self):
        super().__init__('delsys_processor')

        self.declare_parameter('input_topic', 'delsys-data')
        self.declare_parameter('output_topic', 'delsys-data/processed')

        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.pub = self.create_publisher(Float32MultiArray, output_topic, 10)
        self.sub = self.create_subscription(Float32MultiArray, input_topic, self.cb, 10)

        self.get_logger().info(f"Listening on: {input_topic}")
        self.get_logger().info(f"Publishing to: {output_topic}")

    def cb(self, msg: Float32MultiArray):
        # ----- PLACEHOLDER PROCESSING -----
        # Example: rectification + simple gain (replace with your real pipeline)
        processed = [abs(x) for x in msg.data]          # rectify
        processed = [2.0 * x for x in processed]        # gain
        # ----------------------------------

        out = Float32MultiArray()
        out.data = processed
        self.pub.publish(out)


def main():
    rclpy.init()
    node = DelsysProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
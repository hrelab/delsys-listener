import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class TelemedProcessor(Node):
    def __init__(self):
        super().__init__('telemed_processor')

        self.declare_parameter('input_topic', 'telemed-data')
        self.declare_parameter('output_topic', 'telemed-data/processed')

        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.pub = self.create_publisher(Float32MultiArray, output_topic, 10)
        self.sub = self.create_subscription(Float32MultiArray, input_topic, self.cb, 10)

        self.get_logger().info(f"Listening on: {input_topic}")
        self.get_logger().info(f"Publishing to: {output_topic}")

    def cb(self, msg: Float32MultiArray):
        # ----- PLACEHOLDER PROCESSING -----
        # Example: mean-center the signal (replace with your real pipeline)
        if len(msg.data) == 0:
            return
        mu = sum(msg.data) / float(len(msg.data))
        processed = [x - mu for x in msg.data]
        # ----------------------------------

        out = Float32MultiArray()
        out.data = processed
        self.pub.publish(out)


def main():
    rclpy.init()
    node = TelemedProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
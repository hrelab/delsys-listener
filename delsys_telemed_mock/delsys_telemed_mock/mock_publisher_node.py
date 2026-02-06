import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class MockDelsysTelemedPublisher(Node):
    def __init__(self):
        super().__init__('mock_delsys_telemed_publisher')

        # Topics
        self.declare_parameter('delsys_topic', 'delsys_data')
        self.declare_parameter('telemed_topic', 'telemed_data')

        # Rates (Hz)
        self.declare_parameter('delsys_rate_hz', 2000.0)
        self.declare_parameter('telemed_rate_hz', 100.0)

        # Channel config
        self.declare_parameter('delsys_channels', 16)  # variable channel count
        # telemed is fixed to 1 channel by your requirement

        # Random signal tuning (optional but handy)
        self.declare_parameter('delsys_amp', 1.0)
        self.declare_parameter('telemed_amp', 1.0)
        self.declare_parameter('bias', 0.0)

        self.delsys_topic = self.get_parameter('delsys_topic').value
        self.telemed_topic = self.get_parameter('telemed_topic').value

        self.pub_delsys = self.create_publisher(Float32MultiArray, self.delsys_topic, 10)
        self.pub_telemed = self.create_publisher(Float32MultiArray, self.telemed_topic, 10)

        self._start_timers()

        self.get_logger().info(f"Publishing mock delsys on:   {self.delsys_topic}")
        self.get_logger().info(f"Publishing mock telemed on:  {self.telemed_topic}")

    def _start_timers(self):
        # Create (or recreate) timers based on current parameters
        delsys_rate = float(self.get_parameter('delsys_rate_hz').value)
        telemed_rate = float(self.get_parameter('telemed_rate_hz').value)

        # Guard against invalid rates
        delsys_rate = max(0.1, delsys_rate)
        telemed_rate = max(0.1, telemed_rate)

        self.delsys_period = 1.0 / delsys_rate
        self.telemed_period = 1.0 / telemed_rate

        # Create timers
        self.delsys_timer = self.create_timer(self.delsys_period, self._publish_delsys)
        self.telemed_timer = self.create_timer(self.telemed_period, self._publish_telemed)

        self.get_logger().info(f"delsys_rate_hz={delsys_rate} (period={self.delsys_period:.6f}s)")
        self.get_logger().info(f"telemed_rate_hz={telemed_rate} (period={self.telemed_period:.6f}s)")

    def _publish_delsys(self):
        n_ch = int(self.get_parameter('delsys_channels').value)
        n_ch = max(1, n_ch)

        amp = float(self.get_parameter('delsys_amp').value)
        bias = float(self.get_parameter('bias').value)

        # Random values (Python floats), serialized into Float32MultiArray
        # Using uniform [-amp, amp] so you see both signs before rectification
        data = [bias + amp * random.uniform(-1.0, 1.0) for _ in range(n_ch)]

        msg = Float32MultiArray()
        msg.data = data
        self.pub_delsys.publish(msg)

    def _publish_telemed(self):
        amp = float(self.get_parameter('telemed_amp').value)
        bias = float(self.get_parameter('bias').value)

        # Fixed 1 channel as requested
        data = [bias + amp * random.uniform(-1.0, 1.0)]

        msg = Float32MultiArray()
        msg.data = data
        self.pub_telemed.publish(msg)


def main():
    rclpy.init()
    node = MockDelsysTelemedPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
import math
import random
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class MockDelsysTelemedPublisher(Node):
    def __init__(self):
        super().__init__('mock_delsys_telemed_publisher')

        # Topics
        self.declare_parameter('delsys_topic', '/raw_data/emg')
        self.declare_parameter('telemed_topic', '/raw_data/smg')

        # Rates (Hz)
        self.declare_parameter('delsys_rate_hz', 2000.0)
        self.declare_parameter('telemed_rate_hz', 100.0)

        # Channel config
        self.declare_parameter('delsys_channels', 16)

        # Telemed sine parameters
        self.declare_parameter('telemed_period_sec', 3.0)

        self.delsys_topic = self.get_parameter('delsys_topic').value
        self.telemed_topic = self.get_parameter('telemed_topic').value

        self.delsys_rate = float(self.get_parameter('delsys_rate_hz').value)
        self.telemed_rate = float(self.get_parameter('telemed_rate_hz').value)
        self.telemed_period = float(self.get_parameter('telemed_period_sec').value)

        self.pub_delsys = self.create_publisher(Float32MultiArray, self.delsys_topic, 10)
        self.pub_telemed = self.create_publisher(Float32MultiArray, self.telemed_topic, 10)

        # Time reference for sine wave
        self.t0 = time.monotonic()

        self._start_timers()

        self.get_logger().info(f"Publishing delsys (random [-1,1]) on: {self.delsys_topic}")
        self.get_logger().info(f"Publishing telemed (sine 0→1, T={self.telemed_period}s) on: {self.telemed_topic}")

    def _start_timers(self):
        self.delsys_rate = max(0.1, self.delsys_rate)
        self.telemed_rate = max(0.1, self.telemed_rate)

        self.delsys_timer = self.create_timer(
            1.0 / self.delsys_rate, self._publish_delsys
        )
        self.telemed_timer = self.create_timer(
            1.0 / self.telemed_rate, self._publish_telemed
        )

    # ---------------- Delsys ----------------

    def _publish_delsys(self):
        n_ch = max(1, int(self.get_parameter('delsys_channels').value))

        # Uniform random in [-1, 1]
        data = [random.uniform(-1.0, 1.0) for _ in range(n_ch)]

        msg = Float32MultiArray()
        msg.data = data
        self.pub_delsys.publish(msg)

    # ---------------- Telemed ----------------

    def _publish_telemed(self):
        """
        1-channel sine wave:
          range: 0 → 1
          period: telemed_period_sec
        """
        t = time.monotonic() - self.t0
        omega = 2.0 * math.pi / self.telemed_period

        # Standard sine in [-1,1], mapped to [0,1]
        val = 0.5 * (1.0 + math.sin(omega * t))

        msg = Float32MultiArray()
        msg.data = [val]
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

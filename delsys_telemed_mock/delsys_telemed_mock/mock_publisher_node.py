import math
import random
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from stretch_sim_interfaces.msg import Delsys

KEYS = ["EMG 1", "EMG 2", "EMG 3", "EMG 4", "ACC X", "ACC Y", "ACC Z", "GYRO X", "GYRO Y", "GYRO Z"]

class MockDelsysTelemedPublisher(Node):
    def __init__(self):
        super().__init__('mock_delsys_telemed_publisher')

        # Topics
        self.declare_parameter('delsys_topic', 'raw_data/delsys')
        self.declare_parameter('telemed_topic', 'raw_data/telemed')

        # Rates (Hz)
        self.declare_parameter('delsys_rate_hz', 2000.0)
        self.declare_parameter('telemed_rate_hz', 100.0)

        # Channel config
        self.declare_parameter('delsys_sensors', 1)

        # Telemed sine parameters
        self.declare_parameter('telemed_period_sec', 3.0)

        self.delsys_topic = self.get_parameter('delsys_topic').value
        self.telemed_topic = self.get_parameter('telemed_topic').value

        self.delsys_rate = float(self.get_parameter('delsys_rate_hz').value)
        self.telemed_rate = float(self.get_parameter('telemed_rate_hz').value)
        self.telemed_period = float(self.get_parameter('telemed_period_sec').value)

        self.pub_delsys = self.create_publisher(Delsys, self.delsys_topic, 10)
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
        def appendData(data, name, msgD):
            msgD.sensor_name.append(name)
            msgD.emg1.append(data.get("EMG 1"))
            msgD.emg2.append(data.get("EMG 2"))
            msgD.emg3.append(data.get("EMG 3"))
            msgD.emg4.append(data.get("EMG 4"))
            msgD.acc_x.append(float(data.get("ACC X", float("nan"))))
            msgD.acc_y.append(float(data.get("ACC Y", float("nan"))))
            msgD.acc_z.append(float(data.get("ACC Z", float("nan"))))
            msgD.gyro_x.append(float(data.get("GYRO X", float("nan"))))
            msgD.gyro_y.append(float(data.get("GYRO Y", float("nan"))))
            msgD.gyro_z.append(float(data.get("GYRO Z", float("nan"))))

        msg = Delsys()
        n_ch = max(1, int(self.get_parameter('delsys_sensors').value))

        # Uniform random in [-1, 1] for all data in Delsys() custom message
        for i in range(n_ch):
            data = {k: random.uniform(-1.0, 1.0) for k in KEYS}
            appendData(data, f'Sensor {i}', msg)

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

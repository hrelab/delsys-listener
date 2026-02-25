import math
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from stretch_sim_interfaces.msg import Delsys


class RollingRMS:
    """Per-channel rolling RMS over a fixed window of samples."""
    def __init__(self, window_size: int):
        self.set_window(window_size)
        self.buffers = []
        self.sumsq = []

    def set_window(self, window_size: int):
        if window_size < 1:
            window_size = 1
        self.window_size = int(window_size)

    def reset_channels(self, n_channels: int):
        self.buffers = [deque(maxlen=self.window_size) for _ in range(n_channels)]
        self.sumsq = [0.0 for _ in range(n_channels)]

    def update(self, x_rectified):
        n = len(x_rectified)
        if n == 0:
            return []

        if len(self.buffers) != n or (len(self.buffers) > 0 and self.buffers[0].maxlen != self.window_size):
            self.reset_channels(n)

        out = [0.0] * n
        for i, v in enumerate(x_rectified):
            buf = self.buffers[i]

            # subtract outgoing sample if window full
            if len(buf) == buf.maxlen:
                old = buf[0]
                self.sumsq[i] -= old * old

            buf.append(v)
            self.sumsq[i] += v * v

            denom = float(len(buf))  # use partial window at startup
            out[i] = math.sqrt(self.sumsq[i] / denom)

        return out


class DelsysProcessor(Node):
    def __init__(self):
        super().__init__('delsys_processor')

        self.declare_parameter('input_topic', '/raw_data/emg')
        self.declare_parameter('output_topic', '/processed/emg')

        # sampling rate can vary
        self.declare_parameter('sample_rate_hz', 2000.0)
        self.declare_parameter('rms_window_ms', 100.0)

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        self.fs = float(self.get_parameter('sample_rate_hz').value)
        self.win_ms = float(self.get_parameter('rms_window_ms').value)

        self.window_size = self._compute_window_size(self.fs, self.win_ms)
        self.rms = RollingRMS(self.window_size)

        self.pub = self.create_publisher(Float32MultiArray, output_topic, 10)
        self.sub = self.create_subscription(Float32MultiArray, input_topic, self.cb, 10)

        self.get_logger().info(f"Listening on: {input_topic}")
        self.get_logger().info(f"Publishing to: {output_topic}")
        self._log_window()

        # Optional: support runtime param updates (so you can switch 2000 <-> 2222.2222 without restart)
        self.add_on_set_parameters_callback(self._on_params)

    def _compute_window_size(self, fs_hz: float, win_ms: float) -> int:
        return max(1, int(round(fs_hz * (win_ms / 1000.0))))

    def _log_window(self):
        self.get_logger().info(
            f"Rectify + rolling RMS: fs={self.fs} Hz, window={self.win_ms} ms => N={self.window_size} samples"
        )

    def _on_params(self, params):
        # If sample rate or window changes, update rolling RMS window!
        changed = False
        new_fs = self.fs
        new_win = self.win_ms

        for p in params:
            if p.name == 'sample_rate_hz':
                new_fs = float(p.value)
                changed = True
            elif p.name == 'rms_window_ms':
                new_win = float(p.value)
                changed = True

        if changed:
            self.fs = new_fs
            self.win_ms = new_win
            self.window_size = self._compute_window_size(self.fs, self.win_ms)
            self.rms.set_window(self.window_size)
            # next update() call will auto-reset buffers to new maxlen
            self._log_window()

        return rclpy.parameter.SetParametersResult(successful=True)

    def cb(self, msg: Float32MultiArray):
        # One sample per channel per message (your current setup)
        rectified = [abs(float(x)) for x in msg.data]
        rms_vals = self.rms.update(rectified)

        out = Float32MultiArray()
        out.data = rms_vals
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
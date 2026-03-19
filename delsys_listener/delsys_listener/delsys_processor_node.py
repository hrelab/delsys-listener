import math
from collections import deque

import rclpy
from rclpy.node import Node
from stretch_sim_interfaces.msg import DelsysMsg, EmgMsg, ImuMsg


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
        self.buffers = [deque(maxlen=self.window_size)
                        for _ in range(n_channels)]
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

        self.declare_parameter('input_topic', 'raw_data/delsys')
        self.declare_parameter('output_emg', 'processed/emg')
        self.declare_parameter('output_imu', 'processed/imu')

        # sampling rate can vary
        self.declare_parameter('sample_rate_hz', 2000.0)
        self.declare_parameter('rms_window_ms', 100.0)

        input_topic = self.get_parameter('input_topic').value
        output_emg = self.get_parameter('output_emg').value
        output_imu = self.get_parameter('output_imu').value

        self.fs = float(self.get_parameter('sample_rate_hz').value)
        self.win_ms = float(self.get_parameter('rms_window_ms').value)

        self.window_size = self._compute_window_size(self.fs, self.win_ms)
        self.rms = RollingRMS(self.window_size)

        self.pubEMG = self.create_publisher(EmgMsg, output_emg, 10)
        self.pubIMU = self.create_publisher(ImuMsg, output_imu, 10)
        self.sub = self.create_subscription(
            DelsysMsg, input_topic, self.cb, 10)

        self.get_logger().info(f"Listening on: {input_topic}")
        self.get_logger().info(f"Publishing to: {output_emg} and {output_imu}")
        self._log_window()

        # Optional: support runtime param updates (so you can switch 2000 <-> 2222.2222 without restart)
        self.add_on_set_parameters_callback(self._on_params)

        self.acc_min = [0, 0, 0]
        self.acc_max = [0, 0, 0]

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

    def imu_to_msg(self, out, acc, gyro, sensor):
        out.sensor_name.append(sensor)
        out.acc_x.append(acc[0])
        out.acc_y.append(acc[1])
        out.acc_z.append(acc[2])
        out.gyro_x.append(gyro[0])
        out.gyro_y.append(gyro[1])
        out.gyro_z.append(gyro[2])

        return out

    # TODO:
    def emg_processing():
        pass

    # TODO:
    def imu_processing():
        pass

    def cb(self, msg: DelsysMsg):
        # -------------- SETUP --------------
        nSens = len(msg.sensor_name)
        emgData = []

        outEMG = EmgMsg()
        outIMU = ImuMsg()
        # -----------------------------------

        # ----------------------- EMG PROCESSING HERE -----------------------
        # Combine all sensors into a single list for easy processing
        for i in range(nSens):
            emgData.extend([msg.emg1[i], msg.emg2[i],
                           msg.emg3[i], msg.emg4[i]])

        # Process EMG data
        rectified = [abs(float(x)) for x in emgData]
        rms_vals = self.rms.update(rectified)

        # Put Processed EMG data into correct format
        for i in range(nSens):
            outEMG.sensor_name.append(msg.sensor_name[i])
            outEMG.emg1.append(rms_vals[4*i + 0])
            outEMG.emg2.append(rms_vals[4*i + 1])
            outEMG.emg3.append(rms_vals[4*i + 2])
            outEMG.emg4.append(rms_vals[4*i + 3])

        self.pubEMG.publish(outEMG)
        # -------------------------------------------------------------------

        # ----------------------- IMU PROCESSING HERE -----------------------
        if math.isnan(msg.acc_x[0]):
            # Seperate data
            acc = [msg.acc_x[0], msg.acc_y[0], msg.acc_z[0]]
            gyro = [msg.gyro_x[0], msg.gyro_y[0], msg.gyro_z[0]]
            name = msg.sensor_name[0]

            # Publish data
            outIMU = self.imu_to_msg(outIMU, acc, gyro, name)
            self.pubIMU.publish(outIMU)
        # -------------------------------------------------------------------


def main():
    rclpy.init()
    node = DelsysProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

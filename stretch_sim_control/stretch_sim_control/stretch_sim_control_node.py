import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from stretch_sim_interfaces.msg import StretchSimSignals


class StretchSimControlNode(Node):
    def __init__(self):
        super().__init__('stretch_sim_control')

        self.declare_parameter('delsys_topic', 'delsys/processed_data')
        self.declare_parameter('telemed_topic', 'telemed/processed_data')
        self.declare_parameter('output_topic', 'stretch_sim/signals')

        # Threshold for EMG "active" detection
        self.declare_parameter('emg_threshold', 0.6)

        # NEW: EMG channel handling
        self.declare_parameter('emg_channel_count', 1)   # how many channels to consider
        self.declare_parameter('emg_mode', 'first')      # 'first', 'any', 'all'

        # Refractory period (per EMG channel)
        self.declare_parameter('emg_refractory_sec', 1.0)

        # Per-channel refractory state: next time (ns) a channel is allowed to output True again
        self._next_allowed_ns = []

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
        n_ch = int(self.get_parameter('emg_channel_count').value)
        mode = self.get_parameter('emg_mode').value

        # Safety: clamp channel count
        n_ch = max(1, min(n_ch, len(msg.data)))

        # Threshold EMG channels
        active_channels = [float(x) >= thr for x in msg.data[:n_ch]]

        # --- Refractory gating (per channel) ---
        refractory_sec = float(self.get_parameter('emg_refractory_sec').value)
        refractory_ns = int(refractory_sec * 1e9)
        now_ns = int(self.get_clock().now().nanoseconds)

        # Ensure state matches channel count
        if len(self._next_allowed_ns) != n_ch:
            self._next_allowed_ns = [0] * n_ch

        gated_channels = [False] * n_ch
        for i, is_active in enumerate(active_channels):
            # If still in refractory, force False
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

        out = StretchSimSignals()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = ""
        out.smg = smg
        out.emg = [emg_active]

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
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ---------------- Launch arguments ----------------
    emg_threshold = LaunchConfiguration('emg_threshold')
    emg_channel_count = LaunchConfiguration('emg_channel_count')
    emg_mode = LaunchConfiguration('emg_mode')
    emg_refractory_sec = LaunchConfiguration('emg_refractory_sec')

    sample_rate_hz = LaunchConfiguration('sample_rate_hz')
    rms_window_ms = LaunchConfiguration('rms_window_ms')

    delsys_in = LaunchConfiguration('delsys_in')
    telemed_in = LaunchConfiguration('telemed_in')

    delsys_out = LaunchConfiguration('delsys_out')
    telemed_out = LaunchConfiguration('telemed_out')

    output_topic = LaunchConfiguration('output_topic')

    return LaunchDescription([
        # -------- Declare arguments --------
        DeclareLaunchArgument(
            'delsys_in',
            default_value='delsys/raw_data',
            description='Incoming raw delsys topic',
        ),
        DeclareLaunchArgument(
            'telemed_in',
            default_value='telemed/raw_data',
            description='Incoming raw telemed topic',
        ),
        DeclareLaunchArgument(
            'delsys_out',
            default_value='delsys/processed_data',
            description='Processed delsys output topic',
        ),
        DeclareLaunchArgument(
            'telemed_out',
            default_value='telemed/processed_data',
            description='Processed telemed output topic',
        ),
        DeclareLaunchArgument(
            'output_topic',
            default_value='stretch_sim/signals',
            description='Final StretchSimSignals output topic',
        ),
        DeclareLaunchArgument(
            'sample_rate_hz',
            default_value='2000.0',
            description='Delsys sample rate (Hz) used for RMS window sizing',
        ),
        DeclareLaunchArgument(
            'rms_window_ms',
            default_value='100.0',
            description='RMS window duration (ms) for delsys processing',
        ),
        DeclareLaunchArgument(
            'emg_threshold',
            default_value='0.6',
            description='Threshold applied to (rectified+RMS) EMG signal',
        ),
        DeclareLaunchArgument(
            'emg_channel_count',
            default_value='1',
            description='Number of EMG channels to consider',
        ),
        DeclareLaunchArgument(
            'emg_mode',
            default_value='first',
            description="How to combine EMG channels: 'first', 'any', or 'all'",
        ),
        DeclareLaunchArgument(
            'emg_refractory_sec',
            default_value='1.0',
            description='Per-channel EMG refractory period (seconds)',
        ),

        # -------- Delsys processing --------
        Node(
            package='delsys_listener',
            executable='delsys_processor_node',
            name='delsys_processor',
            output='screen',
            parameters=[{
                'input_topic': delsys_in,
                'output_topic': delsys_out,
                'sample_rate_hz': sample_rate_hz,
                'rms_window_ms': rms_window_ms,
            }],
        ),

        # -------- Telemed processing (pass-through) --------
        Node(
            package='delsys_listener',
            executable='telemed_processor_node',
            name='telemed_processor',
            output='screen',
            parameters=[{
                'input_topic': telemed_in,
                'output_topic': telemed_out,
            }],
        ),

        # -------- Stretch sim control --------
        Node(
            package='stretch_sim_control',
            executable='stretch_sim_control_node',
            name='stretch_sim_control',
            output='screen',
            parameters=[{
                'delsys_topic': delsys_out,
                'telemed_topic': telemed_out,
                'output_topic': output_topic,

                'emg_threshold': emg_threshold,
                'emg_channel_count': emg_channel_count,
                'emg_mode': emg_mode,
                'emg_refractory_sec': emg_refractory_sec,
            }],
        ),
    ])
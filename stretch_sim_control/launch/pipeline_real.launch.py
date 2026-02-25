from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ---------------- Launch arguments ----------------
    # EMG Related
    emg_threshold = LaunchConfiguration('emg_threshold')
    emg_refractory_sec = LaunchConfiguration('emg_refractory_sec')
    sample_rate_hz = LaunchConfiguration('sample_rate_hz')
    rms_window_ms = LaunchConfiguration('rms_window_ms')

    # Delsys Processor Related
    delsys_in = LaunchConfiguration('delsys_in')
    delsys_out_emg = LaunchConfiguration('delsys_out_emg')
    delsys_out_imu = LaunchConfiguration('delsys_out_imu')

    # Telemed Processor Related
    telemed_in = LaunchConfiguration('telemed_in')
    telemed_out = LaunchConfiguration('telemed_out')

    # Sim Control Related
    output_emg = LaunchConfiguration('output_emg')
    output_smg = LaunchConfiguration('output_smg')

    return LaunchDescription([
        # -------- Declare arguments --------
        DeclareLaunchArgument(
            'delsys_in',
            default_value='raw_data/delsys',
            description='Incoming raw delsys topic',
        ),
        DeclareLaunchArgument(
            'telemed_in',
            default_value='raw_data/telemed',
            description='Incoming raw telemed topic',
        ),
        DeclareLaunchArgument(
            'delsys_out_emg',
            default_value='processed/emg',
            description='Processed delsys output topic',
        ),
        DeclareLaunchArgument(
            'delsys_out_imu',
            default_value='processed/imu',
            description='Processed delsys output topic',
        ),
        DeclareLaunchArgument(
            'telemed_out',
            default_value='processed/smg',
            description='Processed telemed output topic',
        ),
        DeclareLaunchArgument(
            'output_emg',
            default_value='stretch_sim/emg',
            description='Final StretchSimSignals EMG output topic',
        ),
        DeclareLaunchArgument(
            'output_smg',
            default_value='stretch_sim/smg',
            description='Final StretchSimSignals SMG output topic',
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
                'output_emg': delsys_out_emg,
                'output_imu': delsys_out_imu,
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
                'delsys_topic': delsys_out_emg,
                'telemed_topic': telemed_out,
                'output_emg': output_emg,
                'output_smg': output_smg,

                'emg_threshold': emg_threshold,
                'emg_refractory_sec': emg_refractory_sec,
            }],
        ),
    ])
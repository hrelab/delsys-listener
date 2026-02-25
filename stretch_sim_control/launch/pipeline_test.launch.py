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

    delsys_rate_hz = LaunchConfiguration('delsys_rate_hz')
    telemed_rate_hz = LaunchConfiguration('telemed_rate_hz')
    delsys_channels = LaunchConfiguration('delsys_channels')

    return LaunchDescription([
        # -------- Declare arguments --------
        DeclareLaunchArgument(
            'emg_threshold',
            default_value='0.6',
            description='Threshold applied to RMS EMG signal',
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
        DeclareLaunchArgument(
            'delsys_rate_hz',
            default_value='2000.0',
            description='Mock delsys publish rate (Hz)',
        ),
        DeclareLaunchArgument(
            'telemed_rate_hz',
            default_value='30.0',
            description='Mock telemed publish rate (Hz)',
        ),
        DeclareLaunchArgument(
            'delsys_channels',
            default_value='4',
            description='Number of delsys channels in mock publisher',
        ),

        # -------- Mock publisher --------
        Node(
            package='delsys_telemed_mock',
            executable='mock_publisher_node',
            name='mock_delsys_telemed_publisher',
            output='screen',
            parameters=[{
                'delsys_topic': 'raw_data/emg',
                'telemed_topic': 'raw_data/smg',
                'delsys_rate_hz': delsys_rate_hz,
                'telemed_rate_hz': telemed_rate_hz,
                'delsys_channels': delsys_channels,
                'telemed_period_sec': 3.0,
            }],
        ),

        # -------- Delsys processing --------
        Node(
            package='delsys_listener',
            executable='delsys_processor_node',
            name='delsys_processor',
            output='screen',
            parameters=[{
                'input_topic': 'raw_data/emg',
                'output_topic': 'processed/emg',
                'sample_rate_hz': delsys_rate_hz,
                'rms_window_ms': 100.0,
            }],
        ),

        # -------- Telemed processing --------
        Node(
            package='delsys_listener',
            executable='telemed_processor_node',
            name='telemed_processor',
            output='screen',
            parameters=[{
                'input_topic': 'raw_data/smg',
                'output_topic': 'processed/smg',
            }],
        ),

        # -------- Stretch sim control --------
        Node(
            package='stretch_sim_control',
            executable='stretch_sim_control_node',
            name='stretch_sim_control',
            output='screen',
            parameters=[{
                'delsys_topic': 'processed/emg',
                'telemed_topic': 'processed/smg',
                'output_emg': 'stretch_sim/emg',
                'output_smg': 'stretch_sim/smg',

                # NEW PARAMS WIRED IN
                'emg_threshold': emg_threshold,
                'emg_channel_count': emg_channel_count,
                'emg_mode': emg_mode,
                'emg_refractory_sec': emg_refractory_sec,
            }],
        ),
    ])

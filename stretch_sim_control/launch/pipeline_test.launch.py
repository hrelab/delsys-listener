from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ---------------- Launch arguments ----------------
    # Mock Publisher Related
    delsys_rate_hz = LaunchConfiguration('delsys_rate_hz')
    telemed_rate_hz = LaunchConfiguration('telemed_rate_hz')
    delsys_sensors = LaunchConfiguration('delsys_sensors')

    # EMG Related
    emg_threshold = LaunchConfiguration('emg_threshold')
    emg_refractory_sec = LaunchConfiguration('emg_refractory_sec')
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
        DeclareLaunchArgument(
            'telemed_rate_hz',
            default_value='30.0',
            description='Frequency of SMG',
        ),
        DeclareLaunchArgument(
            'delsys_rate_hz',
            default_value='2000.0',
            description='Frequency of EMG',
        ),
        DeclareLaunchArgument(
            'delsys_sensors',
            default_value='1',
            description='Number of sensors',
        ),

        # -------- Mock publisher --------
        Node(
            package='delsys_telemed_mock',
            executable='mock_publisher_node',
            name='mock_delsys_telemed_publisher',
            output='screen',
            parameters=[{
                'delsys_topic': delsys_in,
                'telemed_topic': telemed_in,
                'delsys_rate_hz': delsys_rate_hz,
                'telemed_rate_hz': telemed_rate_hz,
                'delsys_sensors': delsys_sensors,
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
                'input_topic': delsys_in,
                'output_emg': delsys_out_emg,
                'output_imu': delsys_out_imu,
                'sample_rate_hz': delsys_rate_hz,
                'rms_window_ms': rms_window_ms,
            }],
        ),

        # -------- Telemed processing --------
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

                # NEW PARAMS WIRED IN
                'emg_threshold': emg_threshold,
                'emg_refractory_sec': emg_refractory_sec,
            }],
        ),
    ])

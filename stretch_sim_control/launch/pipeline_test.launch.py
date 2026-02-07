from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Mock source
        Node(
            package='delsys_telemed_mock',
            executable='mock_publisher_node',
            name='mock_delsys_telemed_publisher',
            output='screen',
            parameters=[{
                'delsys_rate_hz': 2000.0,
                'telemed_rate_hz': 30.0,
                'delsys_channels': 4,
            }],
        ),

        # Delsys processing: rectify + RMS
        Node(
            package='delsys_listener',
            executable='delsys_processor_node',
            name='delsys_processor',
            output='screen',
            parameters=[{
                'sample_rate_hz': 2000.0,
                'rms_window_ms': 100.0,
            }],
        ),

        # Telemed processing: pass-through
        Node(
            package='delsys_listener',
            executable='telemed_processor_node',
            name='telemed_processor',
            output='screen',
        ),

        # Combined control output
        Node(
            package='stretch_sim_control',
            executable='stretch_sim_control_node',
            name='stretch_sim_control',
            output='screen',
            parameters=[{
                'emg_threshold': 0.7,
            }],
        ),
    ])
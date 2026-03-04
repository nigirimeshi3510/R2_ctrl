from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('r2_sldasm_description')
    default_model = PathJoinSubstitution([pkg_share, 'urdf', 'r2_sldasm.urdf.xacro'])
    default_rviz = PathJoinSubstitution([pkg_share, 'rviz', 'r2_sldasm.rviz'])

    model = LaunchConfiguration('model')
    rviz_config = LaunchConfiguration('rviz_config')
    qt_platform = LaunchConfiguration('qt_platform')

    robot_description = {
        'robot_description': ParameterValue(
            Command(['xacro ', model]),
            value_type=str,
        )
    }

    return LaunchDescription([
        DeclareLaunchArgument('model', default_value=default_model),
        DeclareLaunchArgument('rviz_config', default_value=default_rviz),
        DeclareLaunchArgument('qt_platform', default_value='xcb'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[robot_description],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            output='screen',
            additional_env={
                'QT_QPA_PLATFORM': qt_platform,
            },
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            output='screen',
            additional_env={
                'QT_QPA_PLATFORM': qt_platform,
            },
        ),
    ])

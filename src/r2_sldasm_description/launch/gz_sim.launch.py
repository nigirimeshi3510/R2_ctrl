from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('r2_sldasm_description')
    ros_gz_sim_share = FindPackageShare('ros_gz_sim')

    model = LaunchConfiguration('model')
    world = LaunchConfiguration('world')

    default_model = PathJoinSubstitution([pkg_share, 'urdf', 'r2_sldasm.urdf.xacro'])
    default_world = PathJoinSubstitution([pkg_share, 'worlds', 'lift_box_world.sdf'])

    robot_description = {
        'robot_description': ParameterValue(
            Command(['xacro ', model]),
            value_type=str,
        )
    }

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ros_gz_sim_share, 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('model', default_value=default_model),
        DeclareLaunchArgument('world', default_value=default_world),
        gz,
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[robot_description],
        ),
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-name', 'r2_sldasm', '-topic', 'robot_description'],
            output='screen',
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            output='screen',
        ),
    ])

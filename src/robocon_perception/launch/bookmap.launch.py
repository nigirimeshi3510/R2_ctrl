from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "lut_yaml_path",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robocon_perception"), "config", "bookmap_lut.yaml"]
            ),
            description="Path to pixel->cell LUT YAML.",
        ),
        Node(
            package="robocon_perception",
            executable="bookmap_node",
            name="bookmap_node",
            output="screen",
            parameters=[{
                "lut_yaml_path": LaunchConfiguration("lut_yaml_path"),
            }],
        ),
    ])

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        Node(
            package="robocon_perception",
            executable="bookmap_viz_node",
            name="bookmap_viz_node",
            output="screen",
        ),
    ])

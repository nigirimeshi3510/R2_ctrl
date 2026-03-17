from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="robocon_bt_mission",
                executable="mock_plum_world",
                name="mock_plum_world",
                output="screen",
            ),
            Node(
                package="robocon_plum_planner",
                executable="plum_planner",
                name="plum_planner",
                output="screen",
            ),
            Node(
                package="robocon_bt_mission",
                executable="mission_bt",
                name="mission_bt",
                output="screen",
            ),
        ]
    )

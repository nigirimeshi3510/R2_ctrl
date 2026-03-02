from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    lut_yaml_default = PathJoinSubstitution(
        [FindPackageShare("robocon_perception"), "config", "bookmap_lut.yaml"]
    )

    use_bookmap = LaunchConfiguration("use_bookmap")
    use_bookmap_viz = LaunchConfiguration("use_bookmap_viz")
    use_foxglove_bridge = LaunchConfiguration("use_foxglove_bridge")

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_bookmap",
            default_value="true",
            description="Start robocon_perception bookmap_node.",
        ),
        DeclareLaunchArgument(
            "use_bookmap_viz",
            default_value="true",
            description="Start robocon_perception bookmap_viz_node.",
        ),
        DeclareLaunchArgument(
            "use_foxglove_bridge",
            default_value="true",
            description="Start foxglove_bridge node.",
        ),
        DeclareLaunchArgument(
            "lut_yaml_path",
            default_value=lut_yaml_default,
            description="Path to bookmap LUT yaml.",
        ),
        DeclareLaunchArgument(
            "foxglove_port",
            default_value="8765",
            description="WebSocket port for foxglove_bridge.",
        ),
        DeclareLaunchArgument(
            "foxglove_address",
            default_value="0.0.0.0",
            description="Bind address for foxglove_bridge.",
        ),
        Node(
            package="robocon_perception",
            executable="bookmap_node",
            name="bookmap_node",
            output="screen",
            parameters=[{"lut_yaml_path": LaunchConfiguration("lut_yaml_path")}],
            condition=IfCondition(use_bookmap),
        ),
        Node(
            package="robocon_perception",
            executable="bookmap_viz_node",
            name="bookmap_viz_node",
            output="screen",
            condition=IfCondition(use_bookmap_viz),
        ),
        Node(
            package="foxglove_bridge",
            executable="foxglove_bridge",
            name="foxglove_bridge",
            output="screen",
            parameters=[{
                "port": LaunchConfiguration("foxglove_port"),
                "address": LaunchConfiguration("foxglove_address"),
            }],
            condition=IfCondition(use_foxglove_bridge),
        ),
    ])

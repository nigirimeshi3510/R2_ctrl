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
    rviz_config_default = PathJoinSubstitution(
        [FindPackageShare("robocon_bringup"), "config", "perception_bookmap.rviz"]
    )

    use_bookmap = LaunchConfiguration("use_bookmap")
    use_bookmap_viz = LaunchConfiguration("use_bookmap_viz")
    use_rviz = LaunchConfiguration("use_rviz")

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
            "use_rviz",
            default_value="true",
            description="Start rviz2 with project config.",
        ),
        DeclareLaunchArgument(
            "lut_yaml_path",
            default_value=lut_yaml_default,
            description="Path to bookmap LUT yaml.",
        ),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=rviz_config_default,
            description="RViz config file path.",
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
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            arguments=["-d", LaunchConfiguration("rviz_config")],
            condition=IfCondition(use_rviz),
        ),
    ])

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.substitutions import FindPackageShare
from lifecycle_msgs.msg import Transition


def _urg_node(
    *,
    name: str,
    namespace: LaunchConfiguration,
    ip_address: LaunchConfiguration,
    ip_port: LaunchConfiguration,
    frame_id: LaunchConfiguration,
    scan_topic: LaunchConfiguration,
) -> tuple:
    node = LifecycleNode(
        package="urg_node2",
        executable="urg_node2_node",
        name=name,
        namespace=namespace,
        output="screen",
        remappings=[("scan", scan_topic)],
        parameters=[{
            "ip_address": ip_address,
            "ip_port": ip_port,
            "frame_id": frame_id,
            "calibrate_time": False,
            "synchronize_time": False,
            "publish_intensity": False,
            "publish_multiecho": False,
            "error_limit": 4,
            "error_reset_period": 5.0,
            "diagnostics_tolerance": 0.05,
            "diagnostics_window_time": 5.0,
            "time_offset": 0.0,
            "angle_min": -3.14,
            "angle_max": 3.14,
            "skip": 0,
            "cluster": 1,
        }],
    )

    configure_handler = RegisterEventHandler(
        OnProcessStart(
            target_action=node,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(node),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    ),
                ),
            ],
        ),
    )

    activate_handler = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=node,
            start_state="configuring",
            goal_state="inactive",
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(node),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        ),
    )

    return node, configure_handler, activate_handler


def generate_launch_description() -> LaunchDescription:
    rviz_config_default = PathJoinSubstitution(
        [FindPackageShare("robocon_bringup"), "config", "dual_lidar.rviz"]
    )

    left_ns = LaunchConfiguration("left_namespace")
    right_ns = LaunchConfiguration("right_namespace")
    left_ip = LaunchConfiguration("left_ip")
    right_ip = LaunchConfiguration("right_ip")
    left_port = LaunchConfiguration("left_port")
    right_port = LaunchConfiguration("right_port")
    left_frame = LaunchConfiguration("left_frame_id")
    right_frame = LaunchConfiguration("right_frame_id")
    left_scan = LaunchConfiguration("left_scan_topic")
    right_scan = LaunchConfiguration("right_scan_topic")
    use_rviz = LaunchConfiguration("use_rviz")

    left_node, left_configure, left_activate = _urg_node(
        name="urg_node2_left",
        namespace=left_ns,
        ip_address=left_ip,
        ip_port=left_port,
        frame_id=left_frame,
        scan_topic=left_scan,
    )
    right_node, right_configure, right_activate = _urg_node(
        name="urg_node2_right",
        namespace=right_ns,
        ip_address=right_ip,
        ip_port=right_port,
        frame_id=right_frame,
        scan_topic=right_scan,
    )

    left_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_to_laser_left",
        output="screen",
        arguments=[
            "--x", "0.0",
            "--y", "0.24",
            "--z", "0.10",
            "--roll", "0.0",
            "--pitch", "0.0",
            "--yaw", "1.5708",
            "--frame-id", "base_link",
            "--child-frame-id", left_frame,
        ],
    )
    right_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_to_laser_right",
        output="screen",
        arguments=[
            "--x", "0.0",
            "--y", "-0.24",
            "--z", "0.10",
            "--roll", "0.0",
            "--pitch", "0.0",
            "--yaw", "-1.5708",
            "--frame-id", "base_link",
            "--child-frame-id", right_frame,
        ],
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "left_namespace",
            default_value="lidar_left",
            description="Namespace for left urg_node2 instance.",
        ),
        DeclareLaunchArgument(
            "right_namespace",
            default_value="lidar_right",
            description="Namespace for right urg_node2 instance.",
        ),
        DeclareLaunchArgument(
            "left_ip",
            default_value="192.168.0.20",
            description="Left UTM-30LX-EW IP address.",
        ),
        DeclareLaunchArgument(
            "right_ip",
            default_value="192.168.0.10",
            description="Right UTM-30LX-EW IP address.",
        ),
        DeclareLaunchArgument(
            "left_port",
            default_value="10940",
            description="Left UTM-30LX-EW ethernet port.",
        ),
        DeclareLaunchArgument(
            "right_port",
            default_value="10940",
            description="Right UTM-30LX-EW ethernet port.",
        ),
        DeclareLaunchArgument(
            "left_frame_id",
            default_value="laser_left",
            description="frame_id for left LiDAR scan.",
        ),
        DeclareLaunchArgument(
            "right_frame_id",
            default_value="laser_right",
            description="frame_id for right LiDAR scan.",
        ),
        DeclareLaunchArgument(
            "left_scan_topic",
            default_value="/scan_left",
            description="Output topic for left LiDAR LaserScan.",
        ),
        DeclareLaunchArgument(
            "right_scan_topic",
            default_value="/scan_right",
            description="Output topic for right LiDAR LaserScan.",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start rviz2 with dual_lidar config.",
        ),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=rviz_config_default,
            description="RViz config file path.",
        ),
        left_tf,
        right_tf,
        left_node,
        right_node,
        left_configure,
        right_configure,
        left_activate,
        right_activate,
        rviz,
    ])

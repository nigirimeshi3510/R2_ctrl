"""ROS 2 node converting Detection2DArray into robocon BookMap."""

from __future__ import annotations

from pathlib import Path

import rclpy
from rclpy.node import Node
from robocon_interfaces.msg import BookMap
from vision_msgs.msg import Detection2DArray

from robocon_perception.bookmap_core import (
    EMPTY_LABEL,
    FAKE_LABEL,
    R1_LABEL,
    R2_LABEL,
    UNKNOWN_LABEL,
    build_bookmap_arrays,
    detection_from_vision_msg,
    load_lut_regions,
    to_book_type_values,
)


class BookMapNode(Node):
    """Converts detector output to a 12-cell BookMap."""

    def __init__(self) -> None:
        super().__init__("bookmap_node")

        self.declare_parameter("input_topic", "/yolo_detections")
        self.declare_parameter("output_topic", "/book_map")
        self.declare_parameter("confidence_threshold", 0.6)
        self.declare_parameter("default_empty_confidence", 1.0)

        default_lut_path = (
            Path(__file__).resolve().parents[1] / "config" / "bookmap_lut.yaml"
        )
        self.declare_parameter("lut_yaml_path", str(default_lut_path))

        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value
        lut_yaml_path = self.get_parameter("lut_yaml_path").get_parameter_value().string_value

        self._confidence_threshold = (
            self.get_parameter("confidence_threshold").get_parameter_value().double_value
        )
        self._default_empty_confidence = (
            self.get_parameter("default_empty_confidence").get_parameter_value().double_value
        )

        self._regions = load_lut_regions(lut_yaml_path)
        self._enum_mapping = {
            EMPTY_LABEL: BookMap.EMPTY,
            R2_LABEL: BookMap.R2,
            R1_LABEL: BookMap.R1,
            FAKE_LABEL: BookMap.FAKE,
            UNKNOWN_LABEL: BookMap.UNKNOWN,
        }

        self._pub = self.create_publisher(BookMap, output_topic, 10)
        self._sub = self.create_subscription(
            Detection2DArray,
            input_topic,
            self._on_detections,
            10,
        )

        self.get_logger().info(
            f"bookmap_node started: input={input_topic}, output={output_topic}, "
            f"threshold={self._confidence_threshold:.2f}, lut={lut_yaml_path}"
        )

    def _on_detections(self, msg: Detection2DArray) -> None:
        observations = []
        for det in msg.detections:
            parsed = detection_from_vision_msg(det)
            if parsed is not None:
                observations.append(parsed)

        labels, confidences = build_bookmap_arrays(
            detections=observations,
            regions=self._regions,
            confidence_threshold=self._confidence_threshold,
            default_empty_confidence=self._default_empty_confidence,
        )

        out = BookMap()
        out.header = msg.header
        out.book_type = to_book_type_values(labels, self._enum_mapping)
        out.confidence = confidences
        self._pub.publish(out)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = BookMapNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

from pathlib import Path
import xml.etree.ElementTree as ET


def test_bt_xml_is_present_and_parseable():
    xml_path = Path(__file__).resolve().parents[1] / "behavior_trees" / "simple_plum_bt.xml"
    root = ET.parse(xml_path).getroot()

    assert root.tag == "root"
    assert root.attrib["main_tree_to_execute"] == "MainTree"
    assert root.find("./BehaviorTree[@ID='MainTree']") is not None
    assert root.find("./TreeNodesModel/Action[@ID='ObserveAllBooksFromCorridor']") is not None
    assert root.find("./TreeNodesModel/Condition[@ID='CheckRetryAvailable']") is not None

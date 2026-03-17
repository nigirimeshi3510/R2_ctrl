from glob import glob

from setuptools import find_packages, setup

package_name = "robocon_bt_mission"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/behavior_trees", glob("behavior_trees/*.xml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="rui3510",
    maintainer_email="rui0314rui@icloud.com",
    description="Mission behavior tree package for the R2 plum phase",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "mission_bt = robocon_bt_mission.mission_bt_node:main",
            "mock_plum_world = robocon_bt_mission.mock_plum_world_node:main",
        ],
    },
)

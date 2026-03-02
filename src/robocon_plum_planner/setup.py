from glob import glob

from setuptools import find_packages, setup

package_name = "robocon_plum_planner"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="rui3510",
    maintainer_email="rui0314rui@icloud.com",
    description="Plum forest discrete planner with strict safety constraints",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "plum_planner = robocon_plum_planner.plum_planner_node:main",
        ],
    },
)

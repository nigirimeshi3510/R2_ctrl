from glob import glob

from setuptools import find_packages, setup

package_name = 'robocon_localization'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rui3510',
    maintainer_email='rui0314rui@icloud.com',
    description='Dual LaserScan fusion for localization stack',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'scan_fuser = robocon_localization.scan_fuser_node:main',
        ],
    },
)

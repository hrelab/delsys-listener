from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'stretch_sim_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/stretch_sim_control']),
        ('share/stretch_sim_control', ['package.xml']),
        (os.path.join('share', 'stretch_sim_control', 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rosuser',
    maintainer_email='rosuser@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'plot = data_plotter.data_plotter_node:main',
        ],
    },
)

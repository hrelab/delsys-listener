from setuptools import setup

package_name = 'rosbag_recorder'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ajay Anand',
    maintainer_email='writetoajayanand@gmail.com',
    description='A package that records specified topics to a rosbag file',
    license='License',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'record_rosbag = rosbag_recorder.record_rosbag:main',
        ],
    },
)
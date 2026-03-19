#!/bin/bash

while true; do
  echo "To record a rosbag: enter the one identifying key values"
  read -r value1
done

ros2 run rosbag_recorder record_rosbag --ros-args -p topics:="[ '/processed/emg', '/processed/imu', '/processed/smg' ]" \
  -p topic_types:="[ 'stretch_sim_interfaces/msg/EmgMsg', 'stretch_sim_interfaces/msg/ImuMsg', 'stretch_sim_interfaces/msg/SmgMsg', 'std_msgs/msg/String' ]" \
  -p output_path:="./data/rosbag-${value1}"

# ros2 run rosbag_recorder record_rosbag --ros-args\
#  -p topics:="[ '/bus0/ft_sensor0/ft_sensor_readings/wrench', '/emg_topic', '/game_info', '/notes' ]"\
#  -p topic_types:="[ 'geometry_msgs/msg/WrenchStamped', 'interfaces/msg/EmgMessage', 'hrelab_unity_msgs/msg/GameInfo', 'std_msgs/msg/String' ]"\
#  -p output_path:="./LOGS/test_bota_emg_game_notes2"

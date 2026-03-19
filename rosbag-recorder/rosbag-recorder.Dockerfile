FROM osrf/ros:humble-desktop

ARG ROS_USER
ARG R_UID
ARG R_GID

ENV ROS_USER="${ROS_USER}"
ENV R_UID="${R_UID}"
ENV R_GID="${R_GID}"

# Add user from local machine to container
# This user has sudo permissions
# Switch to user after creation
RUN useradd -m $ROS_USER && \
        echo "$ROS_USER:$ROS_USER" | chpasswd && \
        usermod --shell /bin/bash $ROS_USER && \
        usermod -aG sudo $ROS_USER && \
        echo "$ROS_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$ROS_USER && \
        chmod 0440 /etc/sudoers.d/$ROS_USER && \
        usermod  --uid $R_UID $ROS_USER && \
        groupmod --gid $R_GID $ROS_USER

USER $ROS_USER

# Update &/| (and/or) install needed tooling/dependencies
# Create user home directory
RUN sudo apt update -y

RUN sudo apt install -y \
    python3-colcon-common-extensions

RUN mkdir -p /home/$ROS_USER/ros2_ws/src

WORKDIR /home/$ROS_USER
RUN git clone https://github.com/hrelab/iiwa-ros2-sensing-control.git
RUN cp -r iiwa-ros2-sensing-control/rosbag-recorder /home/$ROS_USER/ros2_ws/rosbag-recorder

WORKDIR /home/$ROS_USER/ros2_ws
RUN colcon build

# Creating a single `setup.bash` script.
# This was done because there were errors encountered when attempting to run `.sh` file types because of incorrect file permissions.
# Add contents of both `.sh` setup files to a singular `setup.bash` and give it the correct permissions. 
# This must be ran as root.
USER root
RUN head -n -1 /ros_entrypoint.sh > /tmp.sh \
    && mv /tmp.sh /ros_entrypoint.sh \
    && echo 'source "/home/$ROS_USER/ros2_ws/install/setup.bash"' >> /ros_entrypoint.sh \
    && echo 'exec $@' >> /ros_entrypoint.sh \
    && chmod +x /ros_entrypoint.sh


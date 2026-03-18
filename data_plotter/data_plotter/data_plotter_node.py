import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float64MultiArray
from stretch_sim_interfaces.msg import EmgMsg, SmgMsg, ImuMsg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

EMG_TOPIC = "processed/emg"
IMU_TOPIC = "processed/imu"
SMG_TOPIC = "processed/smg"

class DataVisualizer(Node):
    def __init__(self):
        super().__init__('data_visualizer')
        self.sub_emg = self.create_subscription(EmgMsg, EMG_TOPIC, self.emg_cb, 10)
        self.sub_imu = self.create_subscription(ImuMsg, IMU_TOPIC, self.imu_cb, 10)
        self.sub_smg = self.create_subscription(SmgMsg, SMG_TOPIC, self.smg_cb, 10)

    def plot_data(self, data, myNum, label, myLegend):
        plt.figure(num=myNum)
        plt.plot(data)
        plt.xlabel("Sample Number")
        plt.ylabel(label)
        plt.legend(myLegend)
        plt.show()

    def emg_cb(self, msg: EmgMsg):
        emg = np.array([msg.emg1[0], msg.emg2[0], msg.emg3[0], msg.emg4[0]])
        self.plot_data(emg, 1, "Volatage (mV)", ["EMG A", "EMG B", "EMG C", "EMG D"])

    def imu_cb(self, msg: ImuMsg):
        acc = np.array([msg.acc_x[0], msg.acc_y[0], msg.acc_z[0]])
        gyro = np.array([msg.gyro_x[0], msg.gyro_y[0], msg.gyro_z[0]])
        self.plot_data(acc, 2, "Acceleration (g)", ["X", "Y", "Z"])
        self.plot_data(gyro, 3, "Angular Acceleration (deg/s)", ["X", "Y", "Z"])

    def smg_cb(self, msg: SmgMsg):
        smg = np.array([msg.smg[0]])
        self.plot_data(smg, 4, "SMG (noramlized)", ["SMG"])

def main():
    rclpy.init()
    node = DataVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
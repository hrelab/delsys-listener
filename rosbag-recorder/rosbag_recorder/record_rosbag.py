import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
# from std_msgs.msg import String
from rosbag2_py import StorageOptions, ConverterOptions
#to handle multiple topic subscriptions
from rclpy.callback_groups import ReentrantCallbackGroup

import rosbag2_py

class RosbagRecorder(Node):
    def __init__(self):
        super().__init__('rosbag_recorder')
        
        # Declare parameters (list of topics, topic types, and output path)
        self.declare_parameter('topics', ['/topic1', '/topic2'])
        self.declare_parameter('topic_types',['/type1','/type2'])
        self.declare_parameter('output_path', 'rosbag_data')
        

        self.topics = self.get_parameter('topics').get_parameter_value().string_array_value
        self.topic_types = self.get_parameter('topic_types').get_parameter_value().string_array_value
        self.output_path = self.get_parameter('output_path').get_parameter_value().string_value

        #create a dict of topics and their types
        self.topics_to_types = dict(zip(self.topics,self.topic_types)) 

        # Setup rosbag writer with specified options
        storage_options = rosbag2_py._storage.StorageOptions(uri=self.output_path, storage_id='sqlite3')
        converter_options = rosbag2_py._storage.ConverterOptions('', '')  # Default converter 
        self.writer = rosbag2_py.SequentialWriter() 
        self.writer.open(storage_options, converter_options)
        
        # Create a subscription for each topic
            # ReentrantCallback allows callbacks to run in parallel
        self.callback_group = ReentrantCallbackGroup()
        self.subscribers = []
        for topic, topic_type in self.topics_to_types.items():
            msg_type = self.import_message_type(topic_type)
            topic_info = rosbag2_py._storage.TopicMetadata(
            name=topic,
            type=topic_type,
            serialization_format='cdr')
            self.writer.create_topic(topic_info)
            self.subscribers.append(self.create_subscription(
                msg_type, topic, self.create_callback(topic), 10,
                callback_group=self.callback_group
            ))

    def create_callback(self, topic_name):
        """Creates a callback for each topic."""
        def callback(msg):
            self.writer.write(topic_name, serialize_message(msg), self.get_clock().now().nanoseconds)
        return callback

    def import_message_type(self, topic_type):
        """Dynamically imports the message type from ROS 2, handling types with multiple slashes."""
        # Split by the first '/', which separates package from the type path
        package_name, msg_type_path = topic_type.split('/', 1)
        msg_type_path = msg_type_path.replace('/', '.')
        import_path = ""
        first = 0
        for item in msg_type_path.split('.')[:-1]:
            if first ==1:
                import_path = import_path + "."
            if first==0:
                first=1 
            import_path = import_path + item
        # Import the message module dynamically from the given path
        msg_module = __import__(f'{package_name}.{import_path}', fromlist=[msg_type_path.split('.')[-1]])
        # Return the message class
        return getattr(msg_module, msg_type_path.split('.')[-1])

    def destroy_node(self):
        """Destroys the created node and frees memory"""
        # Close the rosbag writer on shutdown
        self.writer.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RosbagRecorder()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

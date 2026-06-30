#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class JoyTeleop(Node):
    def __init__(self):
        super().__init__('joy_teleop_node')

        # Parameters
        self.declare_parameter('axis_linear', 1)   # Left stick vertical
        self.declare_parameter('axis_angular', 0)  # Left stick horizontal
        self.declare_parameter('scale_linear', 1.0)   # Max linear speed
        self.declare_parameter('scale_angular', 1.0)  # Max angular speed

        self.axis_linear = self.get_parameter('axis_linear').value
        self.axis_angular = self.get_parameter('axis_angular').value
        self.scale_linear = self.get_parameter('scale_linear').value
        self.scale_angular = self.get_parameter('scale_angular').value

        # Subscriber to /joy
        self.sub_joy = self.create_subscription(Joy, '/joy', self.joy_callback, 10)

        # Publisher to /cmd_vel
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)

    def joy_callback(self, msg):
        twist = Twist()

        # Scale and saturate to [-1, 1]
        twist.linear.x = max(-1.0, min(1.0, msg.axes[self.axis_linear] * self.scale_linear))
        twist.angular.z = max(-1.0, min(1.0, msg.axes[self.axis_angular] * self.scale_angular))

        self.pub_cmd.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = JoyTeleop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

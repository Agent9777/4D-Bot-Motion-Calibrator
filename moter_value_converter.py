#! /usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray


class CmdVelToMotor(Node):
    def __init__(self):
        super().__init__('cmdvel_to_motor')

        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.callback,
            10
        )

        self.pub = self.create_publisher(
            Float32MultiArray,
            '/motor',
            10
        )

        # Tune this if robot is too fast/slow
        self.max_speed = 1.0

    def callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        # Differential drive
        left = linear - angular
        right = linear + angular

        # Normalize to [-1, 1]
        max_val = max(abs(left), abs(right), 1.0)
        left /= max_val
        right /= max_val

        # Assign to motors
        FR = right
        FL = left
        BL = left
        BR = right

        motor_msg = Float32MultiArray()
        motor_msg.data = [FR, FL, BL, BR]

        self.pub.publish(motor_msg)

        self.get_logger().info(
            f"cmd_vel → L:{left:.2f} R:{right:.2f} | Motors: {motor_msg.data}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToMotor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
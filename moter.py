import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from gpiozero import Motor, PWMOutputDevice

# Motor setup
class MotorDriver:
    def __init__(self, en, in1, in2):
        self.motor = Motor(forward=in1, backward=in2)
        self.enable = PWMOutputDevice(en)

    def set_speed(self, value):
        value = max(min(value, 1.0), -1.0)

        if value > 0:
            self.motor.forward()
        elif value < 0:
            self.motor.backward()
        else:
            self.motor.stop()

        self.enable.value = abs(value)


class MotorNode(Node):
    def __init__(self):
        super().__init__('motor_node')

        # Your pin mapping
        self.motors = {
            "FR": MotorDriver(17, 27, 22),
            "FL": MotorDriver(10, 9, 11),
            "BL": MotorDriver(14, 15, 18),
            "BR": MotorDriver(13, 19, 26)
        }

        self.order = ["FR", "FL", "BL", "BR"]

        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/motor',
            self.callback,
            10
        )

    def callback(self, msg):
        if len(msg.data) != 4:
            self.get_logger().error("Expected [FR, FL, BL, BR]")
            return

        for i, name in enumerate(self.order):
            self.motors[name].set_speed(msg.data[i])

        self.get_logger().info(f"Motors: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = MotorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
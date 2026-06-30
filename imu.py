import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus2
import time
import math

MPU_ADDR = 0x68

class IMUNode(Node):
    def __init__(self):
        super().__init__('imu_node')

        # I2C bus
        self.bus = smbus2.SMBus(1)

        # Wake MPU
        self.bus.write_byte_data(MPU_ADDR, 0x6B, 0)

        # Publisher
        self.publisher_ = self.create_publisher(Imu, 'imu/data', 10)

        self.prev_time = time.time()
        self.yaw = 0.0

        # Run at 50 Hz
        self.timer = self.create_timer(0.02, self.loop)

    def read_word(self, reg):
        high = self.bus.read_byte_data(MPU_ADDR, reg)
        low = self.bus.read_byte_data(MPU_ADDR, reg + 1)
        value = (high << 8) | low
        if value > 32768:
            value -= 65536
        return value

    def loop(self):
        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now

        # Read accelerometer
        AcX = self.read_word(0x3B)
        AcY = self.read_word(0x3D)
        AcZ = self.read_word(0x3F)

        # Read gyro
        GyX = self.read_word(0x43)
        GyY = self.read_word(0x45)
        GyZ = self.read_word(0x47)

        # Convert to SI units
        ax = (AcX / 16384.0) * 9.81
        ay = -(AcY / 16384.0) * 9.81
        az = -(AcZ / 16384.0) * 9.81

        gx = (GyX / 131.0) * math.pi / 180.0  # rad/s
        gy = -(GyY / 131.0) * math.pi / 180.0
        gz = -(GyZ / 131.0) * math.pi / 180.0

        # Simple yaw integration (prototype)
        self.yaw += gz * dt

        # Convert yaw to quaternion (assuming flat robot)
        qw = math.cos(self.yaw / 2)
        qz = math.sin(self.yaw / 2)

        # Create message
        msg = Imu()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        # Orientation (only yaw for now)
        msg.orientation.w = qw
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = qz

        # Angular velocity
        msg.angular_velocity.x = gx
        msg.angular_velocity.y = gy
        msg.angular_velocity.z = gz

        # Linear acceleration
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az

        # Covariances (basic placeholders)
        msg.orientation_covariance[0] = 0.1
        msg.angular_velocity_covariance[0] = 0.1
        msg.linear_acceleration_covariance[0] = 0.1

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Yaw: {math.degrees(self.yaw):.2f} deg"
        )


def main(args=None):
    rclpy.init(args=args)
    node = IMUNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__=="__main__":
    main()
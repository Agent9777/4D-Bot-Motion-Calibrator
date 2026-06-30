import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32MultiArray


class IMUTestNode(Node):
    def __init__(self):
        super().__init__('imu_test_node')

        self.sub = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.pub = self.create_publisher(Float32MultiArray, '/motor', 10)

        self.raw_imu = 0.0

        # CONFIG 👇
        self.test_side = "LEFT"   # "LEFT" or "RIGHT"
        self.flip_motor = "FL"    # which motor to flip: FL / BL / FR / BR

        self.CAL = {
            "FR": 1,
            "FL": 1,
            "BL": 1,
            "BR": 1
        }

        # Sampling
        self.samples = []
        self.sampling = False
        self.start_time = 0
        self.duration = 2.0

        self.stage = 0  # 0=default, 1=flipped, 2=done

        self.timer = self.create_timer(0.05, self.loop)

    def imu_cb(self, msg):
        self.raw_imu = msg.angular_velocity.z

    # -------- SAMPLING --------
    def start_sampling(self):
        self.samples = []
        self.sampling = True
        self.start_time = self.get_clock().now().nanoseconds / 1e9

    def update_sampling(self):
        if not self.sampling:
            return None

        now = self.get_clock().now().nanoseconds / 1e9
        self.samples.append(self.raw_imu)

        if now - self.start_time >= self.duration:
            self.sampling = False

            mean = sum(self.samples) / len(self.samples)
            var = sum((x - mean) ** 2 for x in self.samples) / len(self.samples)

            return mean, var

        return None

    # -------- MOTOR RUN --------
    def run_motors(self):
        speed = 0.7

        FR = FL = BL = BR = 0

        if self.test_side == "LEFT":
            FL = speed * self.CAL["FL"]
            BL = speed * self.CAL["BL"]

        elif self.test_side == "RIGHT":
            FR = speed * self.CAL["FR"]
            BR = speed * self.CAL["BR"]

        msg = Float32MultiArray()
        msg.data = [FR, FL, BL, BR]
        self.pub.publish(msg)

    # -------- LOOP --------
    def loop(self):

        self.run_motors()

        # DEFAULT TEST
        if self.stage == 0:
            if not self.sampling:
                print("\n--- DEFAULT (both motors normal) ---")
                self.start_sampling()
                return

            result = self.update_sampling()
            if result is None:
                return

            mean, var = result
            print(f"DEFAULT → mean={mean:.5f}, var={var:.5f}")

            # Flip ONLY ONE motor
            print(f"\nFlipping motor: {self.flip_motor}")
            self.CAL[self.flip_motor] *= -1

            self.stage = 1

        # FLIPPED TEST
        elif self.stage == 1:
            if not self.sampling:
                print("\n--- FLIPPED (one motor flipped) ---")
                self.start_sampling()
                return

            result = self.update_sampling()
            if result is None:
                return

            mean, var = result
            print(f"FLIPPED → mean={mean:.5f}, var={var:.5f}")

            self.stage = 2

        elif self.stage == 2:
            print("\n✅ TEST COMPLETE")
            self.stage = 3


def main(args=None):
    rclpy.init(args=args)
    node = IMUTestNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
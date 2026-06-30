import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray


class SmartMotorNode(Node):
    def __init__(self):
        super().__init__('smart_motor_node')

        # ROS
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)
        self.pub = self.create_publisher(Float32MultiArray, '/motor', 10)

        # Motor config
        self.CAL = {
            "FR": {"dir": 1},
            "FL": {"dir": 1},
            "BL": {"dir": 1},
            "BR": {"dir": 1}
        }

        self.motor_order = ["FL", "BL", "FR", "BR"]  # test each motor individually

        # IMU
        self.raw_imu = 0.0
        self.bias = 0.0
        self.bias_samples = []
        self.bias_done = False

        # Sampling
        self.samples = []
        self.sampling = False
        self.sample_start_time = 0.0
        self.sample_duration = 2.0

        # Control
        self.cmd_linear = 0.0
        self.cmd_angular = 0.0

        # Calibration state
        self.phase = 0
        self.motor_index = 0

        self.timer = self.create_timer(0.05, self.loop)

    # ================= CALLBACKS =================
    def imu_cb(self, msg):
        self.raw_imu = msg.angular_velocity.z

    def cmd_cb(self, msg):
        self.cmd_linear = msg.linear.x
        self.cmd_angular = msg.angular.z

    # ================= SAMPLING =================
    def start_sampling(self):
        self.samples = []
        self.sampling = True
        self.sample_start_time = self.get_clock().now().nanoseconds / 1e9

    def update_sampling(self):
        if not self.sampling:
            return None

        now = self.get_clock().now().nanoseconds / 1e9
        self.samples.append(self.raw_imu - self.bias)

        if now - self.sample_start_time >= self.sample_duration:
            self.sampling = False
            return sum(self.samples) / len(self.samples)

        return None

    # ================= LOOP =================
    def loop(self):

        # ---- IMU BIAS ----
        if not self.bias_done:
            self.bias_samples.append(self.raw_imu)
            if len(self.bias_samples) > 50:
                self.bias = sum(self.bias_samples) / len(self.bias_samples)
                self.bias_done = True
                self.get_logger().info("IMU Bias Done")
            return

        # ---- CALIBRATION ----
        if self.phase == 0:
            result = self.calibrate_motor()
            if result == "DONE":
                self.phase = 1

        elif self.phase == 1:
            result = self.check_forward()
            if result == "DONE":
                self.phase = 2

        elif self.phase == 2:
            self.print_calibration()
            self.phase = 3

        else:
            self.normal_control()

    # ================= PER MOTOR CALIBRATION =================
    def calibrate_motor(self):

        if self.motor_index >= len(self.motor_order):
            return "DONE"

        motor = self.motor_order[self.motor_index]

        # INIT
        if not hasattr(self, "stage"):
            self.get_logger().info(f"Testing motor: {motor}")
            self.stage = "DEFAULT"
            self.start_sampling()
            return

        # Run ONLY this motor's side
        values = {"FR": 0, "FL": 0, "BL": 0, "BR": 0}

        if motor in ["FL", "BL"]:
            values["FL"] = 0.8 * self.CAL["FL"]["dir"]
            values["BL"] = 0.8 * self.CAL["BL"]["dir"]
        else:
            values["FR"] = 0.8 * self.CAL["FR"]["dir"]
            values["BR"] = 0.8 * self.CAL["BR"]["dir"]

        self.publish_motor(**values)

        mean = self.update_sampling()
        if mean is None:
            return

        # DEFAULT
        if self.stage == "DEFAULT":
            self.default_mean = mean

            self.get_logger().info(f"{motor} DEFAULT → {abs(mean):.3f}")

            # Flip ONLY this motor
            self.CAL[motor]["dir"] *= -1

            self.stage = "FLIPPED"
            self.start_sampling()
            return

        # FLIPPED
        elif self.stage == "FLIPPED":

            flipped_mean = mean

            default_mag = abs(self.default_mean)
            flipped_mag = abs(flipped_mean)

            print("\n========== DEBUG ==========")
            print(f"{motor} DEFAULT : {default_mag:.3f}")
            print(f"{motor} FLIPPED: {flipped_mag:.3f}")
            print("===========================\n")

            if flipped_mag > default_mag:
                print(f"✔ {motor} → USING FLIPPED")
            else:
                print(f"✔ {motor} → USING DEFAULT")
                self.CAL[motor]["dir"] *= -1

            del self.stage
            self.motor_index += 1
            return

    # ================= FORWARD CHECK =================
    def check_forward(self):

        if not hasattr(self, "forward_stage"):
            self.get_logger().info("Checking forward motion...")

            speed = 0.6
            self.publish_motor(
                FR=speed * self.CAL["FR"]["dir"],
                FL=speed * self.CAL["FL"]["dir"],
                BL=speed * self.CAL["BL"]["dir"],
                BR=speed * self.CAL["BR"]["dir"]
            )

            self.forward_stage = True
            self.start_sampling()
            return

        mean = self.update_sampling()
        if mean is None:
            return

        self.get_logger().info(f"Forward rotation → {abs(mean):.3f}")

        if abs(mean) > 0.2:
            self.get_logger().warn("Spinning → fixing RIGHT side")
            self.CAL["FR"]["dir"] *= -1
            self.CAL["BR"]["dir"] *= -1

        del self.forward_stage
        return "DONE"

    # ================= NORMAL CONTROL =================
    def normal_control(self):

        linear = self.cmd_linear
        angular = self.cmd_angular

        left = linear - angular
        right = linear + angular

        max_val = max(abs(left), abs(right), 1.0)
        left /= max_val
        right /= max_val

        FR = right * self.CAL["FR"]["dir"]
        FL = left  * self.CAL["FL"]["dir"]
        BL = left  * self.CAL["BL"]["dir"]
        BR = right * self.CAL["BR"]["dir"]

        self.publish_motor(FR, FL, BL, BR)

    # ================= PRINT =================
    def print_calibration(self):
        print("\n========== FINAL CALIBRATION ==========")
        for m in ["FL", "FR", "BL", "BR"]:
            print(f"{m}: DIR={self.CAL[m]['dir']}")
        print("======================================\n")

    # ================= PUBLISH =================
    def publish_motor(self, FR=0, FL=0, BL=0, BR=0):
        msg = Float32MultiArray()
        msg.data = [FR, FL, BL, BR]
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SmartMotorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
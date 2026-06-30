# 4D Bot Motion Calibrator

## Overview

The **4D Bot Motion Calibrator** is a motion calibration framework for four-wheel differential drive (4D) robots. It provides a method for calibrating the speed and rotation direction of each drive motor independently, resulting in more accurate and consistent robot motion.

Due to manufacturing tolerances, mechanical friction, wheel alignment, voltage variations, and wear, identical motors rarely perform exactly the same. These differences can cause the robot to drift during straight-line motion or rotate inaccurately. This project determines correction values for each motor, allowing the robot to achieve balanced and predictable movement.

The current implementation is designed for robots whose motors can be controlled independently by the computing device. Native support is provided for L298N motor drivers, while the modular hardware abstraction layer allows the framework to be adapted to other motor controllers with minimal modifications.

---

# Features

* Independent calibration of all four drive motors.
* Motor direction verification and correction.
* Motor speed balancing for improved motion accuracy.
* ROS 2 compatible.
* Controller-based robot operation.
* Modular hardware abstraction layer.
* Native support for L298N motor drivers.

---

# Hardware Requirements

## Robot

* Four-wheel differential drive robot (4D Bot).

## Computing Device

Any computing device capable of running ROS 2 and independently controlling the motors can be used.

The project has been tested using:

* Raspberry Pi 5
* Ubuntu Server 24.04
* ROS 2

Other Linux systems capable of running ROS 2 should also work, although they have not been officially tested.

The computing device must have:

* GPIO access for motor control
* I²C interface for the IMU
* Network connectivity (Wi-Fi or Ethernet)

## Motor Drivers

The current implementation supports **L298N** motor drivers.

Each motor must be connected independently so that every wheel can be controlled separately.

If another motor driver or a microcontroller bridge (Arduino, ESP32, STM32, etc.) is used, only the hardware interface inside `hardware.py` needs to be modified.

## IMU

An IMU must be connected through the **I²C interface**.

The default software assumes the IMU is mounted with:

* **X-axis facing the front of the robot**
* **Z-axis facing downward** (IMU mounted upside down)

Other mounting orientations are supported, but the IMU processing code must be updated to match the new orientation.

## Controller

A compatible game controller must be connected to the Raspberry Pi or to the device communicating with it.

The controller is used to drive the robot during both normal operation and the calibration process.

---

# Network Setup

The computer used to control the robot (laptop or desktop) and the computing device on the robot (for example, the Raspberry Pi) **must be connected to the same local network**.

Before running the software:

1. Connect both the Raspberry Pi and the control computer to the same Wi-Fi network (or the same Ethernet network).
2. Determine the IP address of the Raspberry Pi.
3. Connect to the Raspberry Pi using **SSH** (Linux/macOS) or **PuTTY** (Windows).

The Raspberry Pi IP address can be obtained in several ways:

* Checking your router's connected devices list.
* Looking at your Wi-Fi router management page.
* Using an IP scanner such as `nmap`.

Example:

```bash
nmap -sn 192.168.1.0/24
```

Replace the subnet with your local network if necessary.

Once the Raspberry Pi IP address has been identified, connect to it using SSH:

```bash
ssh <username>@<raspberry_pi_ip>
```

Example:

```bash
ssh ubuntu@192.168.1.25
```

Ensure that SSH is enabled on the Raspberry Pi before attempting to connect.

---

# Default Motor Configuration

```python
self.motors = {
    "FR": MotorDriver(17, 27, 22),
    "FL": MotorDriver(10, 9, 11),
    "BL": MotorDriver(14, 15, 18),
    "BR": MotorDriver(13, 19, 26)
}
```

The GPIO assignments above are the default configuration and may be changed to match your hardware.

---

# Software Requirements

* Python 3
* ROS 2
* ROS 2 Joy package

Install the Joy package using:

```bash
sudo apt install ros-<distro>-joy
```

Replace `<distro>` with your installed ROS 2 distribution.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Agent9777/4D-Bot-Motion-Calibrator.git
```

Navigate to the project directory:

```bash
cd 4D-Bot-Motion-Calibrator
```

---


## File Permissions

Before running the project, ensure that all required shell scripts have executable permissions.

You can make an individual script executable using:

```bash
chmod +x <script_name>.sh
```

Alternatively, to grant executable permissions to all shell scripts in the project directory, run:

```bash
chmod +x *.sh
```

If `run.sh` or any other shell script reports a **Permission denied** error, verify that it has executable permissions before attempting to run it again.

You can check the current permissions of the scripts using:

```bash
ls -l *.sh
```

Executable scripts will have the executable (`x`) permission set, for example:

```text
-rwxr-xr-x run.sh
```


# Running the Project

Start the robot using:

```bash
./run.sh
```

The script launches all required components in the correct order.

To start the motor calibration utility:

```bash
python3 motor_calibration.py
```

Before starting calibration, verify that all four motors are functioning correctly and are capable of rotating in both directions. The calibration process assumes that every motor is operational. If one or more motors are not functioning correctly, calibration may fail or produce incorrect correction values.

---

# Adapting to Different Hardware

The framework has been designed to be portable across different robot platforms.

When using different:

* Motor drivers
* Motor controllers
* Microcontroller bridges
* Communication interfaces
* Sensors

the hardware abstraction layer (`hardware.py`) should be updated accordingly.

Some project scripts also contain hardware-specific assumptions. Depending on your platform, these scripts may require manual modification to match your hardware configuration.

---

# Troubleshooting

If `run.sh` does not start the system correctly, execute each command contained within the script manually.

Running each command individually makes it easier to determine which component is failing and provides more detailed error messages for debugging.

Common causes include:

* Missing ROS 2 packages
* Missing Python dependencies
* Incorrect ROS environment configuration
* Network connectivity issues
* Incorrect IP address
* GPIO permission problems
* Hardware connection issues
* IMU orientation mismatch

After identifying and resolving the issue, `run.sh` can be used again to launch the complete system.

---

# Notes

* Every motor must be independently controllable.
* Ensure all motors are functioning correctly before beginning calibration.
* The default IMU orientation assumes the X-axis points toward the front of the robot and the Z-axis points downward.
* If the IMU is mounted differently, the orientation handling code must be updated.
* A compatible controller is required to operate the robot.
* The Raspberry Pi and the control computer must be connected to the same network.
* The Raspberry Pi IP address must be known before establishing an SSH connection.
* The project currently supports L298N motor drivers. Additional drivers can be integrated by extending the hardware abstraction layer.
* Some scripts may require manual modification when adapting the framework to different hardware.
* The project was developed and tested on a Raspberry Pi 5 running Ubuntu Server 24.04 with ROS 2. Other compatible Linux systems may also work but have not been officially tested.

<p align="center">
  <h1 align="center">🦾 RobotClaw</h1>
  <p align="center">
    <strong>Let AI Control Real Robots — From Code to Physical World in One Line</strong>
  </p>
  <p align="center">
    <a href="https://pypi.org/project/robotclaw/"><img src="https://img.shields.io/pypi/v/robotclaw.svg?style=flat-square&color=blue" alt="PyPI version"></a>
    <a href="https://pypi.org/project/robotclaw/"><img src="https://img.shields.io/pypi/pyversions/robotclaw.svg?style=flat-square" alt="Python versions"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License: MIT"></a>
    <a href="https://pypi.org/project/robotclaw/"><img src="https://img.shields.io/pypi/dm/robotclaw.svg?style=flat-square&color=orange" alt="Downloads"></a>
    <a href="https://github.com/RobotBase/robotclaw/stargazers"><img src="https://img.shields.io/github/stars/RobotBase/robotclaw?style=flat-square&color=yellow" alt="Stars"></a>
  </p>
</p>

---

> 🧠 **One `pip install` away from giving your AI agent a real body.**

**RobotClaw** is a Python robotics framework that bridges AI agents with physical robots. It turns high-level AI commands into real-world servo movements — enabling your AI to walk, wave, dance, and interact with the physical world.

Built for the [OpenClaw](https://openclaw.ai) AI agent platform. Compatible with LOBOT LX series bus servos. Designed for makers, researchers, and anyone who wants to bring robots to life.

```bash
pip install robotclaw
```

## 🎬 What Can You Do?

```python
# Your AI agent says: "让机器人挥手"
# RobotClaw makes it happen in the real world:

from robotclaw import Robot, DEFAULT_CONFIG

with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
    robot.go_home(time_ms=2000)          # Stand up
    robot.set_joint("left_hip_pitch",    # Move a joint
                    position=350, 
                    time_ms=500)
```

```
🤖 User:  "让机器人回到初始位置"
🧠 AI:    → robot.go_home(2000) ✅

🤖 User:  "播放走路动作，2倍速"
🧠 AI:    → player.play(walk_clip, speed=2.0) ✅

🤖 User:  "检查所有舵机的电压"
🧠 AI:    → robot.scan() → 报告电压状态 ✅
```

**No robotics PhD required.** If you can write Python, you can control a robot.

---

## ✨ Why RobotClaw?

| Feature | Description |
|---------|-------------|
| 🧠 **AI-Native** | First-class integration with [OpenClaw](https://openclaw.ai) — AI agents control robots via natural language |
| 🔌 **Plug & Play** | Connect USB, `pip install`, and you're controlling servos in 3 lines of code |
| 🎬 **Motion Teaching** | Record human demonstrations, save as JSON, replay at any speed |
| 🤖 **High-Level API** | Think in joints (`left_hip_pitch`), not raw servo IDs |
| 🛠️ **CLI Tools** | `robotclaw-scan` for diagnostics, `robotclaw-teach` for interactive teaching |
| ⚡ **Thread-Safe** | Production-grade mutex-protected serial communication |
| 🐍 **Pure Python** | Zero compiled dependencies — runs anywhere Python runs |

---

## 🚀 Quick Start

### 1. Install

```bash
pip install robotclaw
```

### 2. Connect & Control

```python
from robotclaw import ServoBus

bus = ServoBus()
bus.connect("COM3", baudrate=115200)

# Move servo to position 500 in 1 second
bus.move(servo_id=1, position=500, time_ms=1000)

# Read current position
pos = bus.read_position(servo_id=1)
print(f"Servo position: {pos}")

bus.disconnect()
```

### 3. Build a Walking Robot

```python
from robotclaw import Robot, DEFAULT_CONFIG

with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
    # All 10 joints to home position
    robot.go_home(time_ms=2000)

    # Control individual joints by name
    robot.set_joint("left_hip_pitch", position=350, time_ms=500)
    robot.set_joint("right_knee", position=600, time_ms=500)

    # Read all joint positions at once
    positions = robot.get_positions()
    print(positions)
```

### 4. Teach Your Robot New Moves

No programming needed — just physically move the robot and record:

```python
from robotclaw import Robot, DEFAULT_CONFIG
from robotclaw.recorder import MotionRecorder, MotionPlayer

with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
    # Step 1: Record a motion by posing the robot
    recorder = MotionRecorder(robot)
    recorder.start_recording("wave_hand")

    robot.unload_all()  # Release servos so you can pose by hand
    input("Pose the robot → Press Enter to capture...")
    recorder.capture_frame()

    input("Next pose → Press Enter...")
    recorder.capture_frame()

    clip = recorder.finish_recording()
    recorder.save(clip, "motions/wave_hand.json")

    # Step 2: Replay at any speed
    robot.load_all()
    player = MotionPlayer(robot)
    player.play(clip, speed=1.5)  # 1.5x speed playback
```

### 5. CLI Tools

```bash
# Discover all connected servos
robotclaw-scan --port COM3

# Interactive motion teaching terminal
robotclaw-teach --port COM3
```

---

## 🧠 AI Integration — The Killer Feature

RobotClaw is designed from the ground up for **AI-driven robotics**. It ships with a built-in [OpenClaw](https://openclaw.ai) skill that lets AI agents understand and control the robot through natural language:

```python
from robotclaw.openclaw_skill import OpenClawSkill

# Register with your AI agent
skill = OpenClawSkill(port="COM3")

# Now your AI can:
# - Move joints by name
# - Play recorded motions
# - Read sensor data (position, voltage, temperature)
# - Perform diagnostic scans
# - Chain complex movement sequences
```

**Use Cases:**
- 🎓 **Education** — Students learn robotics through conversation with AI
- 🏭 **Prototyping** — Rapidly test robot behaviors via natural language
- 🎮 **Entertainment** — AI-controlled robot performances and interactions
- 🔬 **Research** — Quickly iterate on movement patterns without manual coding

---

## 🔧 Supported Hardware

| Component | Specification |
|-----------|---------------|
| **Servos** | LOBOT LX-16A / LX-224 / LX-225 bus servos |
| **Interface** | USB-to-TTL serial adapter |
| **Baudrate** | 115200 (direct) or 9600 (controller board) |
| **Power** | 6–8.4V DC, ≥5A recommended for 10 servos |
| **Default Config** | 10 servos, 5 per leg (biped robot) |

> 💡 **Tip:** More servo types and robot configurations coming soon. PRs welcome!

---

## 📁 Architecture

```
src/robotclaw/
├── __init__.py          # Public API: ServoBus, Robot, DEFAULT_CONFIG
├── servo_bus.py         # LOBOT LX protocol — the low-level driver
├── robot_config.py      # JointConfig, LegConfig, RobotConfig
├── robot.py             # High-level robot controller
├── cli.py               # CLI: robotclaw-scan, robotclaw-teach
├── openclaw_skill.py    # OpenClaw AI agent skill adapter
├── SKILL.md             # OpenClaw skill descriptor
└── recorder/            # Motion teaching subsystem
    ├── motion_data.py   # Keyframe & MotionClip data models
    ├── recorder.py      # Record motions from physical teaching
    └── player.py        # Play back motions with speed control
```

---

## 🗺️ Roadmap

- [x] LOBOT LX bus servo protocol driver
- [x] High-level joint-based robot API
- [x] Motion recording & playback system
- [x] OpenClaw AI agent integration
- [x] CLI diagnostic & teaching tools
- [ ] 🔜 Visual motion editor (web UI)
- [ ] 🔜 Inverse kinematics engine
- [ ] 🔜 Support for more servo protocols (Dynamixel, Feetech)
- [ ] 🔜 ROS 2 bridge
- [ ] 🔜 Reinforcement learning integration

---

## 🤝 Contributing

We welcome contributions from robotics enthusiasts, AI researchers, and Python developers!

```bash
# Clone and install in development mode
git clone https://github.com/RobotBase/robotclaw.git
cd robotclaw
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

See the [CHANGELOG](CHANGELOG.md) for recent updates.

---

## 📄 License

[MIT License](LICENSE) — Use it freely in your projects, commercial or otherwise.

---

<p align="center">
  <strong>Built with ❤️ by the <a href="https://github.com/RobotBase">RobotBase</a> team</strong>
  <br>
  <sub>Making AI-powered robotics accessible to everyone</sub>
</p>

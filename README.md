# 🦾 RobotClaw

> Bridge OpenClaw AI agents with physical servo robots — connecting the digital mind to the physical world.

**RobotClaw** 是一个 Python 库，将 [OpenClaw](https://openclaw.ai) 自主 AI 代理平台与 LOBOT LX 总线舵机机器人深度集成。通过 `pip install robotclaw`，即可让 AI 获得控制物理机器人的能力。

---

## ✨ Features

- 🔌 **LOBOT LX Protocol Driver** — Full implementation of the LX serial bus servo protocol
- 🤖 **High-Level Robot API** — Joint-level control with direction/offset mapping
- 🎬 **Motion Teaching** — Record, save, and playback robot movements with variable speed
- 🧠 **OpenClaw Integration** — Skill adapter for AI agent → robot control
- 🛠️ **CLI Tools** — `robotclaw-scan` for diagnostics, `robotclaw-teach` for interactive teaching
- ⚡ **Thread-Safe** — All serial operations protected by mutex locks

## 📦 Installation

```bash
pip install robotclaw
```


For development:
```bash
pip install robotclaw[dev]
``` 

## 🚀 Quick Start

### Basic Servo Control

```python
from robotclaw import ServoBus

# Connect to servo bus
bus = ServoBus()
bus.connect("COM3", baudrate=115200)

# Move servo ID=1 to position 500 in 1 second
bus.move(servo_id=1, position=500, time_ms=1000)

# Read current position
pos = bus.read_position(servo_id=1)
print(f"Position: {pos}")

bus.disconnect()
```

### High-Level Robot Control

```python
from robotclaw import Robot, DEFAULT_CONFIG

with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
    # All joints to home position
    robot.go_home(time_ms=2000)

    # Move a single joint
    robot.set_joint("left_hip_pitch", position=350, time_ms=500)

    # Read all joint positions
    positions = robot.get_positions()
    print(positions)
```

### Motion Teaching & Playback

```python
from robotclaw import Robot, DEFAULT_CONFIG
from robotclaw.recorder import MotionRecorder, MotionPlayer

with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
    # Record a motion
    recorder = MotionRecorder(robot)
    recorder.start_recording("wave_hand")

    robot.unload_all()          # Let user pose the robot
    input("Press Enter to capture frame 1...")
    recorder.capture_frame()

    input("Press Enter to capture frame 2...")
    recorder.capture_frame()

    clip = recorder.finish_recording()
    recorder.save(clip, "motions/wave_hand.json")

    # Play it back at 1.5x speed
    robot.load_all()
    player = MotionPlayer(robot)
    player.play(clip, speed=1.5)
```

### CLI Tools

```bash
# Scan for connected servos
robotclaw-scan --port COM3

# Interactive motion teaching
robotclaw-teach --port COM3
```

## 🧠 OpenClaw Integration

RobotClaw ships with a built-in [OpenClaw](https://openclaw.ai) skill that allows AI agents to control the robot through natural language commands:

```
You: "让机器人回到初始位置"
AI:  → robot.go_home(2000) ✅

You: "播放走路动作，2倍速"
AI:  → player.play(walk_clip, speed=2.0) ✅

You: "检查所有舵机的电压"
AI:  → robot.scan() → 报告电压状态 ✅
```

## 🔧 Hardware Requirements

| Component | Specification |
|-----------|---------------|
| Servos | LOBOT LX-16A / LX-224 / LX-225 bus servos |
| Interface | USB-to-TTL serial adapter |
| Baudrate | 115200 (direct) or 9600 (controller board) |
| Power | 6-8.4V DC, ≥5A for 10 servos |
| Default Config | 10 servos, 5 per leg (biped) |

## 📁 Project Structure

```
src/robotclaw/
├── __init__.py          # Public API exports
├── servo_bus.py         # LOBOT LX protocol driver
├── robot_config.py      # Hardware configuration
├── robot.py             # High-level robot controller
├── cli.py               # CLI entry points
├── openclaw_skill.py    # OpenClaw skill adapter
├── SKILL.md             # OpenClaw skill descriptor
└── recorder/            # Motion teaching subsystem
    ├── motion_data.py   # Keyframe & MotionClip models
    ├── recorder.py      # Motion recorder
    └── player.py        # Motion player
```

## 🤝 Contributing

Contributions are welcome! Please see the [CHANGELOG](CHANGELOG.md) for recent changes.

```bash
# Clone and install in development mode
git clone https://github.com/RobotBase/robotclaw.git
cd robotclaw
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

## 📄 License

[MIT License](LICENSE)

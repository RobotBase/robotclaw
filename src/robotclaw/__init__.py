"""RobotClaw - Bridge OpenClaw AI agents with physical servo robots.

Connecting the digital mind to the physical world by integrating
OpenClaw autonomous AI agent platform with LOBOT LX bus servo robots.
"""

__version__ = "0.1.1"

from .servo_bus import ServoBus
from .robot_config import JointConfig, LegConfig, RobotConfig, DEFAULT_CONFIG
from .robot import Robot

__all__ = [
    "__version__",
    "ServoBus",
    "JointConfig",
    "LegConfig",
    "RobotConfig",
    "DEFAULT_CONFIG",
    "Robot",
]

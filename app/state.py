# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RobotState:
    status: str = "idle"
    current_action: str = "ready"
    last_error: Optional[str] = None
    homed: bool = False
    current_position: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    retrieved_bins: List[str] = field(default_factory=list)
    action_log: List[str] = field(default_factory=list)

    def set_busy(self, action: str) -> None:
        self.status = "busy"
        self.current_action = action
        self.last_error = None

    def set_idle(self, action: str = "ready") -> None:
        self.status = "idle"
        self.current_action = action

    def set_error(self, message: str) -> None:
        self.status = "error"
        self.last_error = message
        self.current_action = "error"
        self.action_log.append(message)

    def log(self, message: str) -> None:
        self.action_log.append(message)

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "current_action": self.current_action,
            "last_error": self.last_error,
            "homed": self.homed,
            "current_position": self.current_position,
            "retrieved_bins": self.retrieved_bins,
            "action_log": self.action_log[-10:],
        }


state = RobotState()

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from .exceptions import ApprovalStepError

class WorkflowState:
    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

@dataclass
class ApprovalStep:
    name: str
    role_name: str
    required: bool = True
    deadline_hours: int = 48
    def deadline(self, start: datetime) -> datetime:
        return start + timedelta(hours=self.deadline_hours)

@dataclass
class ApprovalTask:
    step: ApprovalStep
    assignee_id: str
    created_at: datetime
    completed: bool = False
    comment: str = ""
    def complete(self, comment: str = "") -> None:
        if self.completed:
            raise ApprovalStepError("Задача уже завершена")
        self.completed = True
        self.comment = comment

@dataclass
class ApprovalRoute:
    name: str
    steps: List[ApprovalStep] = field(default_factory=list)
    def first_step(self) -> ApprovalStep:
        if not self.steps:
            raise ApprovalStepError("Маршрут пуст")
        return self.steps[0]
    def next_step(self, current: ApprovalStep) -> Optional[ApprovalStep]:
        if current not in self.steps:
            raise ApprovalStepError("Текущий шаг не принадлежит маршруту")
        idx = self.steps.index(current) + 1
        return self.steps[idx] if idx < len(self.steps) else None

@dataclass
class WorkflowTransition:
    src: str
    dst: str
    reason: str = ""

@dataclass
class Notification:
    message: str
    recipient_id: str
    created_at: datetime

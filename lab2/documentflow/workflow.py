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
    order: int = 0
    
    def deadline(self, start: datetime) -> datetime:
        return start + timedelta(hours=self.deadline_hours)
    
    def is_overdue(self, start: datetime) -> bool:
        """Check if step is overdue"""
        return datetime.utcnow() > self.deadline(start)
    
    def extend_deadline(self, additional_hours: int) -> None:
        """Extend deadline by additional hours"""
        self.deadline_hours += additional_hours

@dataclass
class ApprovalTask:
    step: ApprovalStep
    assignee_id: str
    created_at: datetime
    completed: bool = False
    comment: str = ""
    completed_at: datetime | None = None
    
    def complete(self, comment: str = "") -> None:
        if self.completed:
            raise ApprovalStepError("Задача уже завершена")
        self.completed = True
        self.comment = comment
        self.completed_at = datetime.utcnow()
    
    def reassign(self, new_assignee_id: str) -> None:
        """Reassign task to another user"""
        if self.completed:
            raise ApprovalStepError("Нельзя переназначить завершенную задачу")
        self.assignee_id = new_assignee_id
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return self.step.is_overdue(self.created_at)

@dataclass
class ApprovalRoute:
    name: str
    steps: List[ApprovalStep] = field(default_factory=list)
    is_active: bool = True
    
    def first_step(self) -> ApprovalStep:
        if not self.steps:
            raise ApprovalStepError("Маршрут пуст")
        return self.steps[0]
    
    def next_step(self, current: ApprovalStep) -> Optional[ApprovalStep]:
        if current not in self.steps:
            raise ApprovalStepError("Текущий шаг не принадлежит маршруту")
        idx = self.steps.index(current) + 1
        return self.steps[idx] if idx < len(self.steps) else None
    
    def add_step(self, step: ApprovalStep) -> None:
        """Add a step to the route"""
        self.steps.append(step)
    
    def remove_step(self, step: ApprovalStep) -> None:
        """Remove a step from the route"""
        if step in self.steps:
            self.steps.remove(step)
    
    def get_step_count(self) -> int:
        """Get total number of steps"""
        return len(self.steps)

@dataclass
class WorkflowTransition:
    src: str
    dst: str
    reason: str = ""
    actor_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_valid_transition(self) -> bool:
        """Check if this is a valid state transition"""
        valid_transitions = {
            WorkflowState.NEW: [WorkflowState.IN_REVIEW, WorkflowState.ARCHIVED],
            WorkflowState.IN_REVIEW: [WorkflowState.APPROVED, WorkflowState.REJECTED, WorkflowState.NEW],
            WorkflowState.APPROVED: [WorkflowState.ARCHIVED],
            WorkflowState.REJECTED: [WorkflowState.NEW, WorkflowState.ARCHIVED],
            WorkflowState.ARCHIVED: [WorkflowState.NEW]
        }
        return self.dst in valid_transitions.get(self.src, [])

@dataclass
class Notification:
    message: str
    recipient_id: str
    created_at: datetime
    is_read: bool = False
    priority: int = 0
    
    def mark_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
    
    def is_high_priority(self) -> bool:
        """Check if notification is high priority"""
        return self.priority > 5

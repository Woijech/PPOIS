from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set

@dataclass(frozen=True)
class Permission:
    code: str
    description: str = ""

@dataclass
class Role:
    name: str
    permissions: Set[Permission] = field(default_factory=set)
    def allows(self, code: str) -> bool:
        return any(p.code == code for p in self.permissions)

@dataclass
class Department:
    name: str
    cost_center: str

@dataclass
class AccessPolicy:
    allowed_roles: Set[str] = field(default_factory=set)
    def can_access(self, roles: List[Role]) -> bool:
        return any(r.name in self.allowed_roles for r in roles)

@dataclass
class Organization:
    name: str
    inn: str
    address: str = ""

@dataclass
class User:
    id: str
    login: str
    display_name: str
    is_blocked: bool = False
    roles: List[Role] = field(default_factory=list)
    department: Department | None = None
    org: Organization | None = None
    def has_permission(self, code: str) -> bool:
        return any(r.allows(code) for r in self.roles)
    def assign_role(self, role: Role) -> None:
        if role not in self.roles:
            self.roles.append(role)

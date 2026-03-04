from dataclasses import dataclass
from typing import Optional


@dataclass
class Result:
    name: str
    installed: bool
    manager: Optional[str] = None
    source: Optional[str] = None
    detail: Optional[str] = None

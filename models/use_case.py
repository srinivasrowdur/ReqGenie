"""
Data model for use cases.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class UseCase:
    """Structured representation of a use case"""
    id: str
    title: str
    primary_actor: str
    description: str
    preconditions: List[str]
    main_flow: List[str]
    alternative_flows: List[str]
    postconditions: List[str] 
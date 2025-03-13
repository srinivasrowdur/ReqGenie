"""
Data model for requirements evaluation results.
"""
from dataclasses import dataclass
from typing import Literal, List

@dataclass
class RequirementsEvaluation:
    """Structured evaluation of a requirements document"""
    score: Literal["pass", "needs_improvement"]
    feedback: str
    improvement_areas: List[str] 
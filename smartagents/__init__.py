"""
SmartAgents package for the Requirements Analysis Genie.

This package contains specialized agents for requirements elaboration,
evaluation, use case creation, and processing.
"""

# Version
__version__ = "0.1.0"

from .elaborator_agent import create_elaborator_agent, create_elaboration_prompt
from .evaluator_agent import create_evaluator_agent, create_evaluation_prompt, create_feedback_prompt
from .usecase_agent import create_usecase_agent
from .testcase_agent import create_testcase_agent, create_testcase_prompt
from .code_agent import create_code_agent, create_code_prompt
from .processor_agent import create_processor_agent
from .diagram_agent import create_diagram_agent, create_diagram_prompt


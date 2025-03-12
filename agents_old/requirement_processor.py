"""Requirement Processor

This module implements the deterministic flow orchestration for the 
requirement analysis, validation, and generation process.
"""
import asyncio
from typing import Dict, List, Any, Union, Optional
from agents import trace

from .elaborator_agent import ElaboratorAgent
from .validator_agent import ValidatorAgent
from .finalizer_agent import FinalizerAgent
from .test_generator_agent import TestGeneratorAgent
from .code_generator_agent import CodeGeneratorAgent
from .code_reviewer_agent import CodeReviewerAgent
from .jira_agent import JiraAgent
from .diagram_agent import DiagramAgent

class RequirementProcessor:
    """
    Orchestrates the deterministic flow of requirement processing
    using multiple specialized agents.
    """
    
    def __init__(self):
        """Initialize the processor with all required agents"""
        # Initialize all required agents
        self.elaborator = ElaboratorAgent()
        self.validator = ValidatorAgent()
        self.finalizer = FinalizerAgent()
        self.test_generator = TestGeneratorAgent()
        self.code_generator = CodeGeneratorAgent()
        self.code_reviewer = CodeReviewerAgent()
        self.jira_agent = JiraAgent()
        self.diagram_generator = DiagramAgent()
        
    async def process(self, 
                    requirement: str, 
                    app_type: str, 
                    nfr_content: str = None,
                    jira_config: Dict = None,
                    language: str = "Python",
                    cloud_env: str = "GCP") -> Dict[str, Any]:
        """
        Process the requirement through the entire flow.
        
        Args:
            requirement: The original requirement
            app_type: Application type (Web Application or Web Service)
            nfr_content: Optional NFR document content
            jira_config: Optional Jira configuration for ticket creation
            language: Programming language for code generation
            cloud_env: Cloud environment for architecture
            
        Returns:
            Dict containing the results of each step
        """
        results = {}
        
        # Use a trace to track the entire process
        with trace("ReqGenie Processing Flow"):
            # 1. Initial Analysis (potentially parallel for FR and NFR)
            if nfr_content:
                # Parallel processing for FR and NFR
                elaboration, nfr_analysis = await self.elaborator.process_requirements_parallel(
                    requirement, app_type, nfr_content
                )
                results["elaboration"] = elaboration
                results["nfr_analysis"] = nfr_analysis
            else:
                # Just process the functional requirements
                results["elaboration"] = await self.elaborator.elaborate_requirements(
                    requirement, app_type
                )
                results["nfr_analysis"] = None
            
            # 2. Parallel Validation
            # Validate functional and non-functional requirements in parallel if applicable
            with trace("Validation Phase"):
                validation_tasks = [
                    self.validator.validate_functional(results["elaboration"])
                ]
                
                if results["nfr_analysis"]:
                    validation_tasks.append(
                        self.validator.validate_nfr(results["nfr_analysis"])
                    )
                    
                validation_results = await asyncio.gather(*validation_tasks)
                results["func_validation"] = validation_results[0]
                results["nfr_validation"] = validation_results[1] if len(validation_results) > 1 else None
            
            # 3. Finalization
            with trace("Finalization Phase"):
                results["final_spec"] = await self.finalizer.finalize_requirements(
                    original_requirement=requirement,
                    elaboration=results["elaboration"],
                    validation=results["func_validation"],
                    nfr_data={
                        "document": nfr_content,
                        "analysis": results["nfr_analysis"],
                        "validation": results["nfr_validation"]
                    } if nfr_content else None
                )
            
            # 4. Parallel Generation
            # Generate tests, code, and diagrams in parallel
            with trace("Generation Phase"):
                generation_results = await asyncio.gather(
                    self.test_generator.generate(results["final_spec"]),
                    self.code_generator.generate(results["final_spec"], language),
                    self.diagram_generator.generate(results["final_spec"], app_type, cloud_env)
                )
                
                results["tests"] = generation_results[0]
                results["code"] = generation_results[1]
                results["diagrams"] = generation_results[2]
            
            # 5. Code Review
            with trace("Review Phase"):
                results["review"] = await self.code_reviewer.review(results["code"])
            
            # 6. Optional Jira Integration
            if jira_config:
                with trace("Jira Integration"):
                    results["jira"] = await self.jira_agent.create_tickets(
                        results["final_spec"], 
                        results["tests"], 
                        jira_config
                    )
            
        # Return all results
        return results 
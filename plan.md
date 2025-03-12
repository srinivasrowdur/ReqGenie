# ReqGenie Agent Architecture Redesign Plan (Updated)

## Overview
This document outlines the restructuring of ReqGenie's agent architecture based on established patterns from the Examples framework. The new architecture will replace the swarm framework with the openai-agents SDK and incorporate deterministic flows, specialized agents, parallelization, and guardrails to create a more robust and efficient system.

## 1. Core Agent Structure

### Base Agents
1. **ElaboratorAgent**
   - Primary role: Initial requirement analysis and elaboration
   - Pattern: Input guardrails for requirement validation
   - Implements: Deterministic flow for breaking down requirements

2. **ValidatorAgent**
   - Primary role: Requirement validation and quality checks
   - Pattern: LLM-as-a-judge pattern
   - Parallel validation of functional and non-functional requirements

3. **FinalizerAgent**
   - Primary role: Final requirement specification
   - Pattern: Output guardrails
   - Quality assurance checks before finalization

4. **TestGeneratorAgent**
   - Primary role: Test case generation
   - Pattern: Deterministic flow with parallel generation
   - Multiple test scenarios generated concurrently

5. **CodeGeneratorAgent**
   - Primary role: Code generation
   - Pattern: Agents as tools for specialized language generation
   - Parallel generation for different components

6. **CodeReviewerAgent**
   - Primary role: Code review and quality assurance
   - Pattern: LLM-as-a-judge for code quality
   - Parallel review of different code sections

7. **JiraAgent**
   - Primary role: Jira integration and ticket management
   - Pattern: Tool-based agent for external integration
   - Asynchronous ticket creation and updates

8. **DiagramAgent**
   - Primary role: Architecture and diagram generation
   - Pattern: Deterministic flow for diagram creation
   - Parallel processing for different diagram types

## 2. SDK Migration Strategy

### A. Replace Swarm with openai-agents SDK
```python
# Old swarm imports
from swarm import Agent, Swarm, RunContextWrapper, GuardrailFunctionOutput, input_guardrail, output_guardrail

# New openai-agents imports
from agents import Agent, Runner, RunContextWrapper, GuardrailFunctionOutput, input_guardrail, output_guardrail
```

### B. Architectural Patterns Implementation

1. **Deterministic Flows**
```python
import asyncio
from agents import Agent, Runner, trace

async def process_requirement(requirement):
    # Use trace to track the entire process
    with trace("ReqGenie Processing Flow"):
        # 1. Initial Analysis
        elaboration_result = await Runner.run(
            elaborator_agent,
            requirement
        )
        
        # 2. Validation
        validation_result = await Runner.run(
            validator_agent, 
            elaboration_result.final_output
        )
        
        # ... continue with the flow
```

2. **Input Guardrails**
```python
from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, input_guardrail

class RequirementGuardrailOutput(BaseModel):
    is_valid: bool
    reasoning: str
    suggestions: List[str] = []

@input_guardrail
async def validate_requirement_format(
    context: RunContextWrapper[None], 
    agent: Agent, 
    input_data: str
) -> GuardrailFunctionOutput:
    # Implementation of guardrail logic
    # ...
    return GuardrailFunctionOutput(
        output_info=validation_result,
        tripwire_triggered=not validation_result.is_valid
    )
```

3. **Parallelization**
```python
async def validate_all_requirements(functional_req, nfr_req):
    func_result, nfr_result = await asyncio.gather(
        Runner.run(validator_agent, functional_req),
        Runner.run(validator_agent, nfr_req)
    )
    return func_result, nfr_result
```

## 3. Implementation Steps

1. **Phase 1: SDK Migration**
   - Update requirements.txt to use openai-agents
   - Replace swarm imports with openai-agents imports
   - Update agent initialization to use the new API

2. **Phase 2: Agent Refactoring**
   - Refactor each agent to use the new SDK
   - Implement guardrails using the openai-agents pattern
   - Adapt structured outputs to work with the new SDK

3. **Phase 3: Orchestration Updates**
   - Implement the deterministic flow using Runner.run
   - Update parallel processing to use asyncio.gather with Runner.run
   - Implement traces for better process tracking

4. **Phase 4: UI Integration**
   - Update the Streamlit app to work with the new agent outputs
   - Implement proper async/await patterns for Streamlit
   - Update error handling to work with the new SDK

## 4. Benefits of Migration

1. **Improved Patterns Support**
   - Native support for the patterns shown in Examples
   - Better guardrails implementation
   - More robust structured output handling

2. **Performance Improvements**
   - Native support for parallelization
   - Better async/await patterns
   - Improved error handling

3. **Future Compatibility**
   - Using the latest SDK from OpenAI
   - Better positioned for future upgrades
   - Access to the latest features

## 5. Updated Architecture Diagram

```
┌─────────────────┐          ┌───────────────┐
│                 │          │               │
│  Streamlit UI   │◄─────────┤  RequirementProcessor   │
│                 │          │               │
└─────────────────┘          └───────┬───────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │                 │
                            │  Agents System  │
                            │                 │
                            └────────┬────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      │              │              │
                ┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
                │          │   │          │   │          │
                │ Elaborator│   │ Validator │   │ Finalizer │
                │          │   │          │   │          │
                └──────────┘   └──────────┘   └──────────┘
                      │              │              │
                      └──────────────┼──────────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      │              │              │
                ┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
                │   Test   │   │   Code   │   │   Jira   │
                │ Generator│   │ Generator│   │ Integration│
                └──────────┘   └──────────┘   └──────────┘
```

## Next Steps
1. Begin Phase 1 implementation: SDK migration
2. Update BaseAgent class to use openai-agents SDK
3. Refactor ElaboratorAgent as the first example
4. Build the new RequirementProcessor using deterministic flow pattern 
"""
Import Test Script

This script tests importing all the agent classes to ensure there are no import issues.
"""

# Add the current directory to the path to make local imports work
import os
import sys
import importlib.util

print(f"Python paths: {sys.path}")

# First, check if we can import directly from the "agents" package from the venv
print("\nTesting venv imports...")
site_packages_dir = os.path.join("venv", "lib", "python3.11", "site-packages")
agents_in_venv = os.path.join(site_packages_dir, "agents")
print(f"Looking for agents in: {agents_in_venv}")
print(f"Path exists: {os.path.exists(agents_in_venv)}")

# Check agents package
if importlib.util.find_spec("agents"):
    print("Module 'agents' can be imported")
    try:
        import agents
        print(f"Imported agents package: {agents.__file__}")
        try:
            from agents import Agent, Runner
            print("✓ Successfully imported Agent and Runner")
        except Exception as e:
            print(f"Failed to import Agent/Runner: {e}")
    except Exception as e:
        print(f"Failed to import agents: {e}")
else:
    print("Module 'agents' not found")

# Check openai_agents package    
if importlib.util.find_spec("openai_agents"):
    print("Module 'openai_agents' can be imported")
    try:
        import openai_agents
        print(f"Imported openai_agents package: {openai_agents.__file__}")
    except Exception as e:
        print(f"Failed to import openai_agents: {e}")
else:
    print("Module 'openai_agents' not found")
    
print("\nImport test complete!") 
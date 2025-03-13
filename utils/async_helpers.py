"""
Utility functions for working with asynchronous code.
"""
import asyncio

def run_async(coroutine):
    """Run an async function from a synchronous context.
    
    Args:
        coroutine: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coroutine)
    finally:
        pass  # Don't close the loop as Streamlit may reuse it 
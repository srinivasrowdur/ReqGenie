"""
Utility functions for handling streaming content.
"""
import traceback
import streamlit as st
from openai.types.responses import ResponseTextDeltaEvent

async def stream_content_to_placeholder(stream, placeholder, debug=False, debug_container=None):
    """Helper function to stream content to a Streamlit placeholder.
    
    Args:
        stream: The stream to read events from
        placeholder: The Streamlit placeholder to write content to
        debug: Whether to log debug information
        debug_container: The Streamlit container to write debug info to
        
    Returns:
        The full response text
    """
    full_response = ""
    
    try:
        async for event in stream.stream_events():
            if debug and debug_container:
                with debug_container:
                    st.write(f"Event type: {event.type}")
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                delta = event.data.delta
                if delta:
                    full_response += delta
                    placeholder.markdown(full_response)
        
        return full_response
    except Exception as e:
        placeholder.error(f"Error during streaming: {str(e)}")
        if debug and debug_container:
            with debug_container:
                st.error(f"Streaming error: {traceback.format_exc()}")
        return full_response 
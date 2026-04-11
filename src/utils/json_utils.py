"""
JSON Extraction Utilities

Provides robust methods for extracting and parsing JSON from LLM responses,
handling common formatting issues like markdown blocks, preambles, and 
incomplete responses.
"""

import json
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> Optional[dict[str, Any]]:
    """
    Extracts and parses JSON from an LLM response string.
    
    Tries multiple strategies:
    1. Look for ```json ... ``` blocks
    2. Look for ``` ... ``` blocks
    3. Look for anything between first { and last }
    4. Try to parse the whole string
    
    Args:
        content: The raw string response from the LLM
        
    Returns:
        The parsed dictionary if successful, None otherwise
    """
    if not content or not isinstance(content, str):
        return None
        
    content = content.strip()
    
    # Strategy 1: Search for JSON in markdown code blocks
    # Specifically looking for ```json ... ``` or ``` ... ```
    blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    for block in blocks:
        try:
            # Clean up potential extra whitespace or common LLM hallucinations
            block_clean = block.strip()
            return json.loads(block_clean)
        except json.JSONDecodeError:
            continue

    # Strategy 2: Look for anything between the first '{' and the last '}'
    # This is useful when the LLM adds text before or after the JSON
    try:
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Try to parse the whole string directly
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
        
    logger.warning(f"Could not extract valid JSON from LLM response (first 100 chars): {content[:100]}...")
    return None


def clean_llm_json(data: dict[str, Any], schema_defaults: dict[str, Any]) -> dict[str, Any]:
    """
    Cleans and validates a parsed JSON dictionary against expected defaults.
    Ensures required fields exist and types are correct.
    
    Args:
        data: The dictionary to clean
        schema_defaults: Dictionary of field names to default values
        
    Returns:
        Cleaned dictionary containing at least the default fields
    """
    result = schema_defaults.copy()
    
    if not isinstance(data, dict):
        return result
        
    for key, default_value in schema_defaults.items():
        if key in data:
            # Basic type checking if types match or if default is None
            if default_value is None or isinstance(data[key], type(default_value)):
                result[key] = data[key]
            # Try type conversion if appropriate
            elif isinstance(default_value, float) and isinstance(data[key], (int, float)):
                result[key] = float(data[key])
            elif isinstance(default_value, str):
                result[key] = str(data[key])
                
    return result

"""
Serialization Utilities

Provides helpers for sanitizing data structures for serialization.
Handles numpy types that are not msgpack/json serializable.
"""

import numpy as np
from typing import Any


def sanitize_for_serialization(obj: Any) -> Any:
    """
    Recursively convert numpy types to standard Python types.
    
    Args:
        obj: Any object (dict, list, primitive, or numpy type)
        
    Returns:
        Sanitized object safe for serialization
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_serialization(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_serialization(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif obj is np.nan:
        return None
    else:
        return obj

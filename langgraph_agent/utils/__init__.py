"""
Utils Package
Exports para utilidades y helpers
"""

from .meta_api import get_account, initialize_meta_api
from .helpers import safe_int_from_insight, safe_float_from_insight, format_currency
from .destination_classifier import (
    extract_destination,
    classify_destinations_in_list,
    aggregate_by_destination,
    get_top_destinations
)

__all__ = [
    # Meta API
    "get_account",
    "initialize_meta_api",
    # Helpers
    "safe_int_from_insight",
    "safe_float_from_insight",
    "format_currency",
    # Destination Classifier
    "extract_destination",
    "classify_destinations_in_list",
    "aggregate_by_destination",
    "get_top_destinations",
]
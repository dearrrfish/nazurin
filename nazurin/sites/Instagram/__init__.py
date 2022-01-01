"""Bibliogram (Instagram Proxy) site plugin."""
from .api import Instagram
from .config import PRIORITY
from .interface import handle, patterns

__all__ = ['Instagram', 'PRIORITY', 'patterns', 'handle']

"""
API v1 module initialization
"""

from api.v1 import health, chat, agents, rag, admin

__all__ = [
    "health",
    "chat",
    "agents",
    "rag",
    "admin",
]

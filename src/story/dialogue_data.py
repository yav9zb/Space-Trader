"""Authored dialogue, keyed by node id. Content is added per campaign phase;
tests/test_story_data.py validates the whole graph (see story/dialogue.py).
"""

from typing import Dict

from .dialogue import Node

NODES: Dict[str, Node] = {}

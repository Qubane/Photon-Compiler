"""
Some helper classes
"""


from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """
    Token class
    """

    type: str
    value: Any

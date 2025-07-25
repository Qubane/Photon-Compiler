"""
Some helper classes
"""


from enum import Enum
from typing import Any
from dataclasses import dataclass


class Datatype(Enum):
    """
    Token datatype
    """

    STR = "string"
    INT = "integer"


@dataclass(frozen=True)
class Token:
    """
    Token class
    """

    type: Datatype
    value: Any


@dataclass
class TokenLine:
    """
    Container for multiple tokens
    """

    tokens: list[Token]
    reference_line: int = -1

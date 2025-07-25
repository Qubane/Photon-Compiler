"""
Some helper classes
"""


from enum import Enum
from typing import Any, Union, Iterable
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


@dataclass
class LinkedNode:
    """
    Node for linked list
    """

    value: Any

    next_node: Union["LinkedNode", None] = None


class LinkedList:
    """
    Linked list class
    """

    def __init__(self, iterable: list):
        self.start_node: LinkedNode = LinkedNode(iterable[0])
        self._iter_node: LinkedNode = self.start_node

        current_node = self.start_node
        for item in iterable:
            # define next node
            node = LinkedNode(item)

            # assign next node to previous node
            current_node.next_node = node

            # reassign next node to be the current one
            current_node = node

    def __iter__(self):
        self._iter_node = self.start_node
        return self

    def __next__(self):
        if self._iter_node is None:
            raise StopIteration
        value = self._iter_node.value
        self._iter_node = self._iter_node.next_node
        return value

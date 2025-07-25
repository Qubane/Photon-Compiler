"""
Compiles the code
"""


from source.classes import *


class Compiler:
    """
    Compiler class
    """

    def __init__(self):
        self._label_map: dict[str, LinkedNode] = {}

    def compile(self, parsed_code: list[TokenLine]) -> list[TokenLine]:
        """
        Compiles parsed code
        :param parsed_code: parsed code
        :return: compiled code
        """

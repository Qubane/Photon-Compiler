"""
Source code parser
"""


from source.classes import *


class Parser:
    """
    Parser class
    """

    def __init__(self):
        ...

    def parse(self, code: str) -> list[TokenLine]:
        """
        Parses given code
        :param code: source code
        :return: parsed list of TokenLine's
        """

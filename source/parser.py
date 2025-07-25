"""
Source code parser
"""


from source.classes import *


class Parser:
    """
    Parser class
    """

    @staticmethod
    def parse(code: str) -> list[TokenLine]:
        """
        Parses given code
        :param code: source code
        :return: parsed list of TokenLine's
        """

        # define token and list of tokens
        token = ""
        token_lines = []

        # go through each line
        for line_idx, code_line in enumerate(code.splitlines()):
            # remove comments from code line
            code_line = code_line.split(";", maxsplit=1)[0].strip()

            # skip empty lines
            if len(code_line) == 0:
                continue

            # define token line
            token_line = TokenLine([], line_idx)

            # go through each character in line
            for code_char in (code_line + " "):
                # if space is encountered -> append new token
                if code_char == " ":
                    token_line.tokens.append(Token(Datatype.STR, token))
                    token = ""

                # otherwise append token to list
                else:
                    token += code_char

            # append token line to list
            token_lines.append(token_line)

        # return list
        return token_lines

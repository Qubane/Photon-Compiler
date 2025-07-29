"""
Compiles the code
"""


import math
from source.classes import *


class Compiler:
    """
    Compiler class
    """

    with_args: dict[str, int] = {
        "lda": 0, "movc": 1, "mov": 1}
    without_args: dict[str, int] = {
        "ca": 8, "add": 9, "sub": 10, "and": 11, "or": 12, "xor": 13, "rd": 14, "wt": 15}
    built_ins: set[str] = {
        "jmp", "jmpc", "halt", "load"}

    def __init__(self):
        self._label_map: dict[str, int] = {}

    def _offset_labels(self, starting: int, by: int):
        """
        Offsets all labels from starting index, by some amount
        :param starting: starting index
        :param by: offset amount
        """

        for label_key, label_value in self._label_map.items():
            if label_value > starting:
                self._label_map[label_key] += by

    def compile(self, parsed_code: list[TokenLine]) -> list[TokenLine]:
        """
        Compiles parsed code
        :param parsed_code: parsed code
        :return: compiled code
        """

        # compiled code
        compiled_code = parsed_code

        # perform compilation stages
        compiled_code = self._compile_1(compiled_code)

        # iteratively apply second stage
        old_count = 1
        while old_count != len(compiled_code):
            old_count = len(compiled_code)
            compiled_code = self._compile_2(compiled_code)

        # return compiled code
        return compiled_code

    def _compile_1(self, code: list[TokenLine]) -> list[TokenLine]:
        """
        1st compilation stage
        """

        # make new compiled code
        compiled_code: list[TokenLine] = []

        for idx, token_line in enumerate(code):
            ref_line: int = token_line.reference_line + 1

            # decode instruction
            instruction: str = token_line[0].lower()

            # check instructions with args
            if instruction in self.with_args:
                # check for correct number of arguments
                if len(token_line) < 2:
                    raise TypeError("Missing argument", ref_line)

                # check for correct arguments
                if instruction == "lda":
                    # try converting to integer
                    try:
                        token_line[1] = int(token_line[1], 2)
                    except ValueError:
                        raise ValueError("Unable to decode numeric", ref_line)
                elif instruction == "movc" or instruction == "mov":
                    # check for correct destination
                    destination = token_line[1].lower()
                    if destination == "br" and instruction == "movc":  # conditional move to br
                        token_line[1] = 0
                    elif destination == "mr":
                        token_line[1] = 1
                    elif destination == "pc":
                        token_line[1] = 2
                    elif destination == "br" and instruction == "mov":  # unconditional move to br
                        token_line[1] = 3
                    else:
                        raise NameError("Undefined destination", ref_line)

            # name check argless and built ins
            elif instruction in self.without_args or instruction in self.built_ins:
                pass

            # labels
            elif instruction[-1] == ":":
                # link label to linked node
                self._label_map[token_line[0][:-1]] = idx
                continue

            # name error
            else:
                raise NameError("Undefined instruction", ref_line)

            # append token line
            compiled_code.append(token_line)

        # return compiled code
        return compiled_code

    def _compile_2(self, code: list[TokenLine]) -> list[TokenLine]:
        """
        2nd compilation stage
        """

        # make new compiled code
        compiled_code: list[TokenLine] = []

        for idx, token_line in enumerate(code):
            ref_line: int = token_line.reference_line + 1

            # decode instruction
            instruction: str = token_line[0].lower()

            if instruction in self.built_ins:
                # unconditional jump
                if instruction == "jmp" or instruction == "jmpc":
                    # check argument number
                    if len(token_line) < 2:
                        raise TypeError("Missing argument", ref_line)

                    # check label name
                    if token_line[1] not in self._label_map:
                        raise NameError("Undefined jump label", ref_line)

                    # instruction count
                    instruction_count = len(compiled_code)

                    # unroll instructions
                    compiled_code.append(TokenLine(["CA"]))     # clear ACC

                    # if it's an unconditional jump
                    if instruction == "jmp":
                        compiled_code.append(TokenLine(["AND"]))    # clear carry flag

                    # append jump address
                    compiled_code.append(TokenLine(["LOAD", self._label_map[token_line[1]]]))

                    # append jump
                    compiled_code.append(TokenLine(["MOVC", 2]))

                    # offset other labels
                    self._offset_labels(idx, len(compiled_code) - instruction_count)

                elif instruction == "halt":
                    # instruction count
                    instruction_count = len(compiled_code)

                    # unroll instructions
                    compiled_code.append(TokenLine(["CA"]))  # clear ACC
                    compiled_code.append(TokenLine(["AND"]))  # clear carry flag

                    # append jump address (current index)
                    compiled_code.append(TokenLine([
                        "LOAD", len(compiled_code) + math.ceil(math.log2(len(compiled_code))) - 1]))

                    # append jump
                    compiled_code.append(TokenLine(["MOVC", 2]))

                    # offset other labels
                    self._offset_labels(idx, len(compiled_code) - instruction_count)

                elif instruction == "load":
                    # check argument number
                    if len(token_line) < 2:
                        raise TypeError("Missing argument", ref_line)

                    # instruction count
                    instruction_count = len(compiled_code)

                    # unroll instructions
                    compiled_code.append(TokenLine(["CA"]))  # clear ACC

                    # decode integer, always assume base 10
                    try:
                        number = int(token_line[1])
                    except ValueError:
                        raise ValueError("Unable to decode integer", ref_line)

                    # insert nibble loading instructions
                    insert_index = len(compiled_code)
                    while number > 0:
                        compiled_code.insert(insert_index, TokenLine(["LDA", number & 3]))
                        number >>= 2

                    # offset other labels
                    self._offset_labels(idx, len(compiled_code) - instruction_count)

            # ignore other instructions
            else:
                compiled_code.append(token_line)

        # return compiled code
        return compiled_code

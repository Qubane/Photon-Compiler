"""
Compiles the code
"""


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
        "jmp"}

    def __init__(self):
        self._label_map: dict[str, LinkedNode] = {}

    def compile(self, parsed_code: list[TokenLine]) -> list[TokenLine]:
        """
        Compiles parsed code
        :param parsed_code: parsed code
        :return: compiled code
        """

        # linked tokens
        linked_code = LinkedList(parsed_code)

        # perform compilation stages
        self._compile_1(linked_code)

        # return compiled code
        return [x.value for x in linked_code]

    def _compile_1(self, code: LinkedList):
        """
        1st compilation stage
        """

        for linked_line in code:
            linked_line: LinkedNode
            token_line: TokenLine = linked_line.value
            ref_line: int = token_line.reference_line

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
                        token_line[1] = int(token_line[1])
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
                self._label_map[token_line[0][:-1]] = linked_line

            # name error
            else:
                raise NameError("Undefined instruction", ref_line)

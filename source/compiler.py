"""
Simple compiler for Photon CPU
"""


from copy import deepcopy
from source.classes import *


COMPILER_SPACERS = {
    " "}
COMPILER_LINE_SPACER = "\n"
COMPILER_COMMENT_OPERATOR = "#"
COMPILER_OPERATORS = {
    ":", ";", "!",
    "+", "-", "*", "/", "(", ")", "<<", ">>", "&", "|", "^", "=",
    "==", "!=", "<", ">"}
COMPILER_OPERATORS.add(COMPILER_LINE_SPACER)
COMPILER_OPERATORS.add(COMPILER_COMMENT_OPERATOR)
COMPILER_BUILT_INS = {
    "if", "else", "for", "while", "end"}
COMPILER_OPEN_CLAUSE = {
    "if", "for", "while"}
COMPILER_END_CLAUSE = {
    "end"}


class Lexer:
    """
    Reads the input, and converts it into simple sequence
    """

    @staticmethod
    def code_to_tokens(code: str) -> list[str]:
        """
        Converts code into tokens
        :param code: code
        :return: list of tokens
        """

        # find overlaps
        operator_overlaps = {x[0] for x in COMPILER_OPERATORS if (x[0] != x and x[0] in COMPILER_OPERATORS)}
        multi_char_ops = {x for x in COMPILER_OPERATORS if len(x) > 1}

        # do magic
        idx = 0
        token = ""
        output = []
        while idx < len(code) and (char := code[idx]):
            idx += 1
            if char in COMPILER_SPACERS or char in COMPILER_OPERATORS:
                if token:
                    output.append(token)
                    token = ""
                if char in COMPILER_OPERATORS:
                    # if the operator overlaps, search for longest one the code may cover
                    if char in operator_overlaps:
                        max_len = 1
                        operator = char
                        for op in multi_char_ops:
                            if code[idx-1:idx+len(op)-1] == op and len(op) > max_len:
                                operator = op
                                max_len = len(op)
                        output.append(operator)
                        idx += max_len - 1
                    else:
                        output.append(char)
            else:
                token += char
        if token:
            output.append(token)

        # output
        return output

    @staticmethod
    def tokens_to_struct(tokens: list[str]) -> list[list[str]]:
        """
        Converts token sequence into a sequence of token lines
        :param tokens: token list
        :return: token struct
        """

        tokens = deepcopy(tokens)

        stack = []
        output = []
        while tokens and (token := tokens.pop(0)):
            if token == COMPILER_LINE_SPACER:
                if stack:
                    output.append(stack[::])
                    stack.clear()
            elif token == COMPILER_COMMENT_OPERATOR:
                while tokens.pop(0) != COMPILER_LINE_SPACER:
                    pass
            else:
                stack.append(token)
        if stack:
            output.append(stack)
        return output

    @staticmethod
    def infix_to_rpn(expression: str) -> list[str]:
        """
        Infix math notation to reverse polish notation
        :param expression: infix string
        :return: rpn token sequence
        """

        # convert expression to tokens
        expression = Lexer.code_to_tokens(expression)

        # lowest -> highest
        precedence = {
            "=": 0,
            ">": 1,
            "<": 1,
            "==": 1,
            "!=": 1,
            "|": 2,
            "^": 3,
            "&": 4,
            "<<": 5,
            ">>": 5,
            "+": 6,
            "-": 6,
            "*": 7,
            "/": 7,
            "**": 8}

        associativity = {
            "=": "R",
            ">": "L",
            "<": "L",
            "==": "L",
            "!=": "L",
            "|": "L",
            "^": "L",
            "&": "L",
            "<<": "R",
            ">>": "R",
            "+": "L",
            "-": "L",
            "*": "L",
            "/": "L",
            "**": "R"}

        stack = []
        output = []
        for token in expression:
            if token not in COMPILER_OPERATORS:
                output.append(token)
            elif token == "(":
                stack.append(token)
            elif token == ")":
                # pop from stack until opening parenthesis is found
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                stack.pop()  # remove the remaining parenthesis
            else:
                while stack and stack[-1] != "(" and (
                        precedence[stack[-1]] > precedence[token] or
                        (precedence[stack[-1]] == precedence[token] and associativity[token] == 'L')
                ):
                    output.append(stack.pop())
                stack.append(token)
        output += stack[::-1]
        return output


class Compiler:
    """
    Main Compiler class
    """

    def __init__(self, **kwargs):
        self.output: list[PhotonIS] = []

        self.bit_width: int = 12
        self._max_int: int = 2 ** self.bit_width - 1

        self.variable_counter: int = 0
        self.variable_mapper: dict[str, int] = {}

        self.temp_var: str = "__temp__"
        self.swap_var: str = "__swap__"
        self.allocate_var(self.temp_var)
        self.allocate_var(self.swap_var)

        self.function_mapper: dict[str, int] = {}

        for name, value in kwargs.items():
            setattr(self, name, value)

    def __copy__(self):
        excluded = {"output"}
        _dict = {key: deepcopy(value) for key, value in self.__dict__.items() if key not in excluded}
        return self.__class__(**_dict)

    def create_function(self, name: str, index: int) -> None:
        """
        Creates a function
        :param name: function name
        :param index: function jump index
        """

        self.function_mapper[name] = index

    def function_mapper_update(self, index: int, index_offset: int) -> None:
        """
        Update function index pointer
        :param index: start index
        :param index_offset: index offset
        """

        for key, value in self.function_mapper.items():
            if index_offset > 0:
                if value > index:
                    self.function_mapper[key] += index_offset
            else:
                if value < index:
                    self.function_mapper[key] += index_offset

    def allocate_var(self, var: str) -> None:
        """
        Allocates a variable
        :param var: variable name
        """

        if var not in self.variable_mapper:
            self.variable_mapper[var] = self.variable_counter
            self.variable_counter += 1

    def merge(self, instructions: list[PhotonIS]) -> None:
        """
        Merge instructions
        :param instructions: list of instructions
        """

        self.function_mapper_update(len(self.output) - 1, len(instructions))
        self.output += instructions

    def add(self, asm: str) -> None:
        """
        Adds new instruction to output
        :param asm: sequence of assembly instructions
        """

        start_length = len(self.output)
        asm = asm.split(" ")
        while asm and (token := asm.pop(0)):
            if token not in PHOTON_INSTRUCTION_SET:
                raise Exception("Instruction not found")

            # instructions with operand
            if PHOTON_INSTRUCTION_SET[token] < 8:
                instruction = f"{token}_{asm.pop(0)}"
                self.output.append(getattr(PhotonIS, instruction))
            else:
                self.output.append(getattr(PhotonIS, token))
        self.function_mapper_update(start_length - 1, len(self.output) - start_length)

    def nibble_loading(self, num: str | int) -> tuple[list[int], str]:
        """
        Nibble loading order
        :param num: number
        :return: nibbles, 'L' or 'R' for left and right ordering
        """

        num = int(num) & self._max_int
        nibbles = [(num & (1 << x)) >> x for x in range(self.bit_width - 1, -1, -1)]

        # count same nibbles from right side
        from_right = 0
        first_nibble_right = nibbles[-1]
        for nibble in nibbles[::-1]:
            if nibble == first_nibble_right:
                from_right += 1
            else:
                break

        # count same nibbles from left side
        from_left = 0
        first_nibble_left = nibbles[0]
        for nibble in nibbles:
            if nibble == first_nibble_left:
                from_left += 1
            else:
                break

        if from_right < from_left:
            if first_nibble_left == 1:
                from_left = 0
            return nibbles[from_left:], "R"
        else:
            if first_nibble_right == 1:
                from_right = 0
            return nibbles[::-1][from_right:], "L"

    def load_acc(self, num: str | int, optimal: bool = True) -> None:
        """
        Generate code to load num to ACC
        :param num: number to load
        :param optimal: load using optimal amount of instructions
        """

        if optimal:
            self.add("CA")
        if int(num) == 0:
            return
        if optimal:
            nibbles, order = self.nibble_loading(num)
            if order == "L":
                self.add(" ".join(f"LAL {x}" for x in nibbles))
            else:
                self.add(" ".join(f"LAR {x}" for x in nibbles))
        else:
            num = int(num) & self._max_int
            nibbles = [(num & (1 << x)) >> x for x in range(self.bit_width - 1, -1, -1)]
            self.add(" ".join(f"LAR {x}" for x in nibbles))

    def load_mr(self, num: str | int) -> None:
        """
        Load Memory Register
        :param num: number
        """

        self.add("AND")
        self.load_acc(num)
        self.add("MOVC MR")

    def load_var_addr(self, var: str) -> None:
        """
        Load variable address
        :param var: variable name
        """

        self.load_acc(self.variable_mapper[var])

    def load_var_to_mr(self, var: str) -> None:
        """
        Load variable address to MR
        :param var: variable name
        """

        self.load_mr(self.variable_mapper[var])

    def load_pr(self, offset: str | int, optimal: bool = True) -> None:
        """
        Load jump into PR
        :param offset: offset (can be negative)
        :param optimal: static / dynamic length
        """

        self.load_acc(offset + 2**(self.bit_width - 1), optimal=optimal)
        self.add("MOVC PR")

    def load_var(self, var: str) -> None:
        """
        Loads variable
        :param var: variable name
        """

        self.load_var_to_mr(var)
        self.add("RD")

    def load_auto(self, x: str) -> None:
        """
        Automatically load X
        :param x: variable name or int
        """

        if x == "__ACC__":
            return

        if x.isnumeric():
            self.load_acc(x)
        else:
            self.load_var(x)

    def convert_infix(self, expression: list[str]) -> None:
        """
        Converts infix to instructions
        :param expression: infix expression
        """

        variable_stack = []
        expression = Lexer.infix_to_rpn("".join(expression))
        while expression and (token := expression.pop(0)):
            if token not in COMPILER_OPERATORS:
                variable_stack.append(token)

                # if the previous accumulator value is going to be replaced
                if len(variable_stack) >= 4 and variable_stack[-3] == "__ACC__":
                    self.add("MOV BR")
                    self.load_var_to_mr(self.temp_var)
                    self.add("CA XOR WT")
                    variable_stack[-3] = self.temp_var
            else:
                var1 = variable_stack.pop()
                var2 = variable_stack.pop()

                # make sure var2 always contains token __ACC__
                swapped = False
                if var1 == "__ACC__":
                    var1, var2 = var2, var1
                    swapped = True

                if token == "+":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("ADD")
                    variable_stack.append("__ACC__")
                elif token == "-":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("SUB")
                    if not swapped:
                        self.add("MOV BR CA SUB")
                    variable_stack.append("__ACC__")
                elif token == ">" or token == "<":
                    if (not swapped and token == ">") or (swapped and token == "<"):
                        self.load_auto(var2)
                        self.add("MOV BR")
                        self.load_auto(var1)
                        self.add("SUB")
                    else:
                        self.load_auto(var2)
                        self.add("MOV BR")
                        self.load_var_to_mr(self.swap_var)
                        self.add("CA XOR WT")
                        self.load_auto(var1)
                        self.add("MOV BR")
                        self.load_var_to_mr(self.swap_var)
                        self.add("CA RD SUB")
                    # carry = 0 => A >  B; ACC >= 0; BR = B
                    # carry = 1 => A <= B; ACC >  0; BR = B

                    self.add("CA MOV BR")  # ACC = 0; BR = 0; carry = ?
                    self.add("LAR 1")
                    self.add("MOVC BR")
                    # carry = 0 => ACC = 1; BR = 1
                    # carry = 1 => ACC = 1; BR = 0

                    self.add("XOR")
                    variable_stack.append("__ACC__")
                elif token == "==" or token == "!=":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("XOR")
                    # ACC = 0 if A == B
                    # ACC > 0 if A != B

                    self.add("MOV BR CA SUB")
                    # CF = 0 if A == B
                    # CF = 1 if A != B

                    self.add("CA MOV BR LAR 1")  # write 0 to BR, write 1 to ACC
                    self.add("MOVC BR")
                    if token == "==":
                        self.add("AND")
                    else:
                        self.add("XOR")
                    # if CF = 0, then ACC = 1
                    # if CF = 1, then ACC = 0

                    # if CF is 0, then MOVC BR will copy 1 to BR, and when bitwise AND of ACC and BR is done
                    # since ACC == BR == 1, the result will be 1
                    # if CF is 1, then MOVC BR will not copy 1 to BR, and BR will be 0, and when bitwise AND is done
                    # since ACC == 1 and BR == 0, the result will be 0
                elif token == "<<" or token == ">>":
                    if swapped:
                        raise NotImplementedError
                    if not var1.isnumeric():
                        raise NotImplementedError

                    self.load_auto(var2)
                    for _ in range(int(var1)):
                        if token == "<<":
                            self.add("LAR 0")
                        else:
                            self.add("LAL 0")
                    variable_stack.append("__ACC__")
                elif token == "&":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("AND")
                    variable_stack.append("__ACC__")
                elif token == "|":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("OR")
                    variable_stack.append("__ACC__")
                elif token == "^":
                    self.load_auto(var2)
                    self.add("MOV BR")
                    self.load_auto(var1)
                    self.add("XOR")
                    variable_stack.append("__ACC__")
                elif token == "=":
                    self.add("MOV BR")
                    self.allocate_var(var1)
                    self.load_var_to_mr(var1)
                    self.add("CA XOR WT")

    def fetch_clause(self, asm: list[list[str]], end_at: set[str] | None = None) -> tuple[list[list[str]], list[str]]:
        """
        Fetches clause from given list.
        NOTE: it pops data from given list directly.
        :param asm: assembly code
        :param end_at: end at instruction
        :return: clause and last line
        """

        if end_at is None:
            end_at = COMPILER_END_CLAUSE

        stack = []
        depth = 0
        while True:
            line = asm.pop(0)
            stack.append(line)
            if line[0] in COMPILER_OPEN_CLAUSE:
                depth += 1
            elif line[0] in end_at:
                if depth == 0:
                    stack.pop()
                    break
                depth -= 1

        return stack, line

    def compile(self, asm: list[list[str]]) -> list[PhotonIS]:
        """
        Compiles the given assembly code structure
        :param asm: assembly struct
        :return: bytecode
        """

        asm = deepcopy(asm)
        while asm and (line := asm.pop(0)):
            if len(line) >= 2 and line[1] == "=":
                # simple assignment
                if len(line) == 3:
                    if not line[2].isnumeric() and line[2] not in self.variable_mapper:
                        raise Exception("Variable called before being assigned")

                    # assign variable and increment memory counter
                    self.allocate_var(line[0])

                    # store variable
                    self.load_var_to_mr(line[0])
                    self.load_auto(line[2])
                    self.add("WT")

                # complex assignment
                else:
                    self.convert_infix(line)
            elif line[0] == "if":
                # fetch clause and make condition
                condition = line[1:]
                stack, last_line = self.fetch_clause(asm, {"end", "else"})
                has_else = last_line[0] == "else"

                # generate condition
                self.convert_infix(condition)
                self.add("MOV BR CA SUB")
                # if CF == 1 then ACC was 1 => don't skip 'if'
                # if CF == 0 then ACC was 0 => skip 'if'

                # compile the code inside the if clause
                compiler_if = self.__copy__()
                compiler_if.compile(stack)

                # if there's an else clause
                compiled_else = []
                if has_else:
                    # fetch clause
                    stack, last_line = self.fetch_clause(asm)

                    # compile code inside else clause
                    compiled_else = self.__copy__().compile(stack)

                    # add code to if clause for jumping over the else clause
                    # without condition
                    compiler_if.add("XOR XOR")
                    compiler_if.load_pr(len(compiled_else))

                # generate jump to skip the if clause
                self.load_pr(len(compiler_if.output))

                # append the if clause
                self.merge(compiler_if.output)

                # append the else clause
                self.merge(compiled_else)
            elif line[0] == "while":
                # fetch clause and make condition
                condition = line[1:]
                stack, last_line = self.fetch_clause(asm)

                # get jump index before the condition
                pre_condition_index = len(self.output) - 1

                # generate condition
                self.convert_infix(condition)
                self.add("MOV BR CA SUB")

                # compile the while clause
                compiler = self.__copy__()
                compiler.compile(stack)

                # create static instruction length unconditional jump
                # offset is formed by:
                # 1. length of code added by while clause (including this jump itself)
                # 2. length of the condition section (including the jump over the while loop)
                # then offset must become a negative one, since we are jumping back
                jump_offset = len(compiler.output) + self.bit_width
                jump_offset += 1  # AND operation
                jump_offset += len(self.output) - pre_condition_index + self.bit_width
                jump_offset = 2**(self.bit_width - 1) - jump_offset - 1

                compiler.add("AND")
                compiler.load_acc(jump_offset, optimal=False)
                compiler.add("MOVC PR")

                # create conditional jump over the while clause
                self.load_pr(len(compiler.output), optimal=False)

                # add the while clause code
                self.merge(compiler.output)

        return self.output

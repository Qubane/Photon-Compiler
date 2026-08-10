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
    ":", ";",
    "+", "-", "*", "/", "(", ")", "<<", ">>", "&", "|", "^", "=",
    "==", "<", ">"}
COMPILER_OPERATORS.add(COMPILER_LINE_SPACER)
COMPILER_OPERATORS.add(COMPILER_COMMENT_OPERATOR)
COMPILER_BUILT_INS = {
    "if", "else", "for", "while", "end"}


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
                        max_len = 0
                        operator = ""
                        for op in COMPILER_OPERATORS:
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

        self.bit_width: int = 8
        self._max_int: int = 2 ** self.bit_width - 1

        self.variable_counter: int = 0
        self.variable_mapper: dict[str, int] = {}

        self.temp_var: str = "__temp__"
        self.swap_var: str = "__swap__"
        self.allocate_var(self.temp_var)
        self.allocate_var(self.swap_var)

        self.jump_indices: list[tuple[int, int]] = []

        for name, value in kwargs.items():
            setattr(self, name, value)

    def __copy__(self):
        _dict = deepcopy(self.__dict__)
        _dict.pop("output")
        return self.__class__(**_dict)

    def allocate_var(self, var: str) -> None:
        """
        Allocates a variable
        :param var: variable name
        """

        if var not in self.variable_mapper:
            self.variable_mapper[var] = self.variable_counter
            self.variable_counter += 1

    def update_jump_indices(self, index: int, offset: int = 1) -> None:
        """
        Updates the jump indices after a given index
        :param index: instruction line index
        :param offset: offset
        """

        for idx, index_tuple in enumerate(self.jump_indices):
            if offset > 1:
                if index >= index_tuple[0]:
                    self.jump_indices[idx] = (self.jump_indices[idx][0] + offset, self.jump_indices[idx][1])
                if index >= index_tuple[1]:
                    self.jump_indices[idx] = (self.jump_indices[idx][0], self.jump_indices[idx][1] + offset)
            else:
                if index <= index_tuple[0]:
                    self.jump_indices[idx] = (self.jump_indices[idx][0] + offset, self.jump_indices[idx][1])
                if index <= index_tuple[1]:
                    self.jump_indices[idx] = (self.jump_indices[idx][0], self.jump_indices[idx][1] + offset)

    def add_jump_index(self, start: int, end: int) -> None:
        """
        Adds a new jump index
        :param start: start index
        :param end: end index
        """

        self.jump_indices.append((start, end))

    def merge(self, instructions: list[PhotonIS]) -> None:
        """
        Merges 2 instruction lists
        :param instructions: list of instructions
        """

        old_len = len(self.output)
        self.output += instructions
        new_len = len(self.output)
        self.update_jump_indices(old_len, new_len - old_len)

    def add(self, asm: str) -> None:
        """
        Adds new instruction to output
        :param asm: sequence of assembly instructions
        """

        old_len = len(self.output)
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
        new_len = len(self.output)
        self.update_jump_indices(old_len, new_len - old_len)

    def load_acc(self, num: str | int) -> None:
        """
        Generate code to load num to ACC
        :param num: number to load
        """

        self.add("CA")
        num = int(num) & self._max_int
        if num == 0:
            return
        nibbles = [(num & (1 << x)) >> x for x in range(self.bit_width-1, -1, -1)]

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

        # use the smaller one
        if from_right < from_left:
            if first_nibble_left == 1:
                from_left = 0
            for nibble in nibbles[::-1][:self.bit_width - from_left]:
                self.add(f"LAR {nibble}")
        else:
            if first_nibble_right == 1:
                from_right = 0
            for nibble in nibbles[:self.bit_width - from_right]:
                self.add(f"LAL {nibble}")

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
                    if swapped:
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
                elif token == "<<":
                    ...
                elif token == ">>":
                    ...
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

    def _compile_generate_jumps(self) -> None:
        """
        Generate jump instructions
        """

        for idx, (start, end) in enumerate(self.jump_indices):
            output_left, output_right = self.output[:start], self.output[start:]
            self.output = output_left

            self.load_acc(end - start + 128)
            self.add("MOVC PR")

            self.output += output_right

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
                condition = line[1:]
                stack = []
                while (line := asm.pop(0))[0] != "end":
                    stack.append(line)
                self.convert_infix(condition)
                self.add("MOV BR CA SUB")
                # if CF == 1 then ACC was 1 => don't skip 'if'
                # if CF == 0 then ACC was 0 => skip 'if'

                start_index = len(self.output)
                # merge compiled instructions from copy of current compiler
                self.merge(self.__copy__().compile(stack))
                end_index = len(self.output)
                self.add_jump_index(start_index, end_index)

        self._compile_generate_jumps()

        return self.output


class Compiler2:
    def __init__(self):
        self.output: list[str] = []

        self.memory_counter: int = 0
        self.memory_assignment: dict[str, int] = {}

        self.temp_var: str = "__temp__"
        self.ensure_variable(self.temp_var)
        self.swap_var: str = "__swap__"
        self.ensure_variable(self.swap_var)

    def push(self, asm: str):
        self.output += asm.split(" ")

    def ensure_variable(self, var: str):
        if var not in self.memory_assignment:
            self.memory_assignment[var] = self.memory_counter
            self.memory_counter += 1

    def load_number(self, number: str | int):
        """
        Generates code for loading an integer
        :param number: number
        """

        # clear ACC
        self.push("CA")

        # compute the nibbles
        number = int(number) & 0xFF
        if number == 0:
            return
        nibbles = [(number & (1 << x)) >> x for x in range(7, -1, -1)]

        # count same nibbles from right side
        from_right = 0
        first_nibble = nibbles[-1]
        for nibble in nibbles[::-1]:
            if nibble == first_nibble:
                from_right += 1
            else:
                break

        # count same nibbles from left side
        from_left = 0
        first_nibble = nibbles[0]
        for nibble in nibbles:
            if nibble == first_nibble:
                from_left += 1
            else:
                break

        # use the smaller one
        if from_right < from_left:
            for nibble in nibbles[::-1][:8 - from_left]:
                self.push(f"LDAR {nibble}")
        else:
            for nibble in nibbles[:8 - from_right]:
                self.push(f"LDAL {nibble}")

    def load_mr(self, addr: str | int):
        """
        Generates code for loading address into MR (Memory Register)
        :param addr: address
        """

        self.push("AND")  # clear carry
        self.load_number(addr)  # load address number
        self.push("MOVC MR")  # move to MR

    def load_var_mr(self, var: str):
        """
        Generated code for loading variable address into MR (Memory Register)
        :param var: variable
        """

        self.load_mr(self.memory_assignment[var])

    def move_var_to_var(self, var1: str, var2: str):
        """
        Generates code for moving var1 to var2
        :param var1: variable 1
        :param var2: variable 2
        """

        self.load_var_mr(var1)  # load address of var1
        self.push("RD")  # read value of var1

        self.push("MOV BR")  # move to BR

        self.load_var_mr(var2)  # load address of var2
        self.push("CA")  # clear ACC
        self.push("XOR")  # move BR to ACC

        self.push("WT")  # write var1 to var2

    def load_auto(self, token: str):
        """
        Generates code to automatically load token (either variable or number)
        :param token: token
        """

        if token == "__ACC__":
            return

        if not token.isnumeric() and token not in self.memory_assignment:
            raise Exception("Variable called before being assigned")

        if token.isnumeric():
            self.load_number(token)
        else:
            self.load_var_mr(token)
            self.push("RD")

    def convert_infix(self, line: list[str]):
        """
        Generates code to convert infix mathematical expression
        :param line: math
        """

        stack = []
        line = infix_to_rpn("".join(line))
        while line and (token := line.pop(0)):
            if token not in COMPILER_OPERATORS:
                stack.append(token)
                if len(stack) >= 4 and stack[-3] == "__ACC__":
                    self.push("MOV BR")  # move ACC to BR
                    self.load_var_mr(self.temp_var)
                    self.push("CA XOR WT")  # move BR to ACC and write
                    stack[-3] = self.temp_var
            else:
                # fetch var1 and var2
                var1 = stack.pop()
                var2 = stack.pop()  # must be ACC or other number

                swapped = False
                if var1 == "__ACC__":
                    swapped = True
                    var1, var2 = var2, var1

                if token == "+":
                    self.load_auto(var2)
                    self.push("MOV BR")
                    self.load_auto(var1)
                    self.push("ADD")
                    stack.append("__ACC__")
                elif token == "-":
                    self.load_auto(var2)
                    self.push("MOV BR")
                    self.load_auto(var1)
                    self.push("SUB")
                    if not swapped:
                        self.push("MOV BR CA SUB")
                    stack.append("__ACC__")
                elif token == ">" or token == "<":
                    if (not swapped and token == ">") or (swapped and token == "<"):
                        self.load_auto(var2)
                        self.push("MOV BR")
                        self.load_auto(var1)
                        self.push("SUB")
                    else:
                        self.load_auto(var2)
                        self.push("MOV BR")
                        self.load_var_mr(self.swap_var)
                        self.push("CA XOR WT")
                        self.load_auto(var1)
                        self.push("MOV BR")
                        self.load_var_mr(self.swap_var)
                        self.push("CA RD SUB")

                    # carry = 0 => A >  B; ACC >= 0; BR = B
                    # carry = 1 => A <= B; ACC >  0; BR = B

                    self.push("CA MOV BR")  # ACC = 0; BR = 0; carry = ?
                    self.push("LDAR 1")
                    self.push("MOVC BR")

                    # carry = 0 => ACC = 1; BR = 1
                    # carry = 1 => ACC = 1; BR = 0
                    self.push("XOR")
                    stack.append("__ACC__")
                elif token == "=":
                    self.push("MOV BR")
                    self.ensure_variable(var1)
                    self.load_var_mr(var1)
                    self.push("CA XOR")  # put BR into ACC
                    self.push("WT")  # write var2 into var1

    @staticmethod
    def line_merge(asm: list[str]) -> list[list[str]]:
        """
        Merges lines of code
        :param asm: asm
        :return: merged code
        """

        output = []
        asm = asm[::]
        while asm and (instruction := asm.pop(0)):
            if COMPILER_INSTRUCTION_SET_MAPPER[instruction] < 8:
                output.append([instruction, asm.pop(0)])
            else:
                output.append([instruction])
        return output

    @staticmethod
    def code_optimize(asm: list[list[str]]) -> list[list[str]]:
        """
        Optimises the generated code
        """

        new_output = []
        asm = deepcopy(asm)

        acc = 0  # ACC
        br = 0  # BR
        mr = 0  # MR
        cf = 0  # CF

        acc_known = False
        br_known = False
        mr_known = False
        cf_known = False

        while asm and (line := asm.pop(0)):
            # fetch instruction
            if COMPILER_INSTRUCTION_SET_MAPPER[line[0]] < 8:
                instruction, operand = line
            else:
                instruction = line[0]
                operand = 0

            if acc_known:
                acc &= 0xFF
            match instruction:
                case "LDAR":
                    if acc_known:
                        acc = (acc << 1) | int(operand)
                    new_output.append(line)
                case "LDAL":
                    if acc_known:
                        acc = (acc >> 1) | (int(operand) << 7)
                    new_output.append(line)
                case "MOVC":
                    if operand == "BR":
                        # if either ACC, BR or CF are unknown
                        # or the ACC != BR and CF != 0
                        if not (acc_known and br_known and cf_known and acc == br and cf == 0):
                            new_output.append(line)
                            br_known = False

                        # if ACC is known and CF == 0
                        # then BR must be equal to ACC
                        if acc_known and cf_known and cf == 0:
                            br_known = True
                            br = acc
                    elif operand == "MR":
                        # if either ACC, MR or CF are unknown
                        # or the ACC != MR and CF != 0
                        if not (acc_known and mr_known and cf_known and acc == mr and cf == 0):
                            new_output.append(line)
                            mr_known = False

                        # if ACC is known and CF == 0
                        # then MR must be equal to ACC
                        if acc_known and cf_known and cf == 0:
                            mr_known = True
                            mr = acc
                    elif operand == "PR":
                        new_output.append(line)
                case "MOV":
                    # if either ACC is unknown or ACC != BR
                    if not (acc_known and acc == br):
                        new_output.append(line)
                        br_known = False

                    # if ACC is known, then BR must be equal ACC
                    if acc_known:
                        br_known = True
                        br = acc
                case "CA":
                    # if either ACC is not known or ACC != 0
                    if not (acc_known and acc == 0):
                        new_output.append(line)

                    # we know ACC must be equal to 0 now
                    acc_known = True
                    acc = 0
                case "ADD":
                    # if either ACC, BR or CF are not known
                    # or BR != 0 (aka not ACC + 0)
                    if not (acc_known and br_known and cf_known and br == 0):
                        new_output.append(line)
                        acc_known = False
                        cf_known = False

                    # if ACC and BR are known, then ACC must equal ACC + BR
                    # and then CF must be known as well
                    if acc_known and br_known:
                        acc += br
                        cf_known = True
                        if acc > 255:
                            cf = 1
                        else:
                            cf = 0
                case "SUB":
                    # if either ACC, BR or CF are not known
                    # or BR != 0 (aka not ACC - 0)
                    if not (acc_known and br_known and cf_known and br == 0):
                        new_output.append(line)
                        acc_known = False
                        cf_known = False

                    # if ACC and BR are known, then ACC must equal ACC - BR
                    # and then CF must be known as well
                    if acc_known and br_known:
                        acc -= br
                        cf_known = True
                        if acc < 0:
                            cf = 1
                        else:
                            cf = 0
                case "AND":
                    # if either ACC, BR or CF are not known
                    if not (acc_known and br_known and cf_known):
                        new_output.append(line)
                        acc_known = False

                    # from CPU definition
                    cf_known = True
                    cf = 0

                    # if ACC and BR are known, then ACC must equal ACC & BR
                    if acc_known and br_known:
                        acc &= br

                    # if BR is known to be 0, then ACC must equal 0 (since any number & 0 is 0)
                    if br_known and br == 0:
                        acc_known = True
                        acc = 0
                case "OR":
                    # if either ACC, BR or CF are not known
                    if not (acc_known and br_known and cf_known):
                        new_output.append(line)
                        acc_known = False

                    # from CPU definition
                    cf_known = True
                    cf = 0

                    # if ACC and BR are known, then ACC must equal ACC | BR
                    if acc_known and br_known:
                        acc |= br
                case "XOR":
                    # if either ACC, BR or CF are not known
                    if not (acc_known and br_known and cf_known):
                        new_output.append(line)
                        acc_known = False

                    # from CPU definition
                    cf_known = True
                    cf = 0

                    # if ACC and BR are known, then ACC must equal ACC ^ BR
                    if acc_known and br_known:
                        acc ^= br
                case "RD":
                    new_output.append(line)
                    acc_known = False
                case "WT":
                    new_output.append(line)

        ptr = -1
        while ptr < len(new_output) - 1:
            ptr += 1
            if COMPILER_INSTRUCTION_SET_MAPPER[new_output[ptr][0]] < 4:
                if ptr >= 1 and new_output[ptr - 1][0] == new_output[ptr + 1][0] == "CA":
                    new_output.pop(ptr)
                    new_output.pop(ptr)
                    ptr -= 2

        return new_output

    def compile(self, structs: list[list[str]]) -> list[list[str]]:
        """
        Compiles structs into asm code
        :param structs: token struct
        :return: asm sequence
        """

        structs = deepcopy(structs)
        while structs and (line := structs.pop(0)):
            # assignment
            if len(line) >= 2 and line[1] == "=":
                # simple assignment
                if len(line) == 3:
                    if not line[2].isnumeric() and line[2] not in self.memory_assignment:
                        raise Exception("Variable called before being assigned")

                    # assign variable and increment memory counter
                    self.ensure_variable(line[0])

                    # store variable
                    if line[2].isnumeric():
                        self.load_var_mr(line[0])  # load variable address
                        self.load_number(line[2])  # load number itself
                        self.push("WT")  # write number at variable address
                    else:
                        self.move_var_to_var(line[2], line[0])

                # complex assignment
                else:
                    self.convert_infix(line)

            # if statement
            elif line[0] == "if":
                condition = line[1:]
                stack = []
                while (line := structs.pop(0))[0] != "end":
                    stack.append(line)
                self.convert_infix(condition)  # generate code for condition
                print(condition, stack)

        # do final steps
        asm = self.line_merge(self.output)
        print(asm)
        asm = self.code_optimize(asm)
        print(asm)

        # return
        return asm

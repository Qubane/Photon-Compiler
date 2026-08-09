"""
Simple compiler for Photon CPU
"""


from copy import deepcopy


COMPILER_SPACERS = {
    " ", ";"}
COMPILER_OPERATORS = {
    ":", "\n", "#",
    "+", "-", "*", "/", "(", ")", "<<", ">>", "&", "|", "^",
    "=", "<", ">"}
COMPILER_BUILT_INS = {
    "if", "else", "for", "while", "end"}
COMPILER_INSTRUCTION_SET = [
    "LDAR",
    "LDAR",
    "LDAL",
    "LDAL",
    "MOVC",
    "MOVC",
    "MOVC",
    "MOV",
    "CA",
    "ADD",
    "SUB",
    "AND",
    "OR",
    "XOR",
    "RD",
    "WT"]
COMPILER_INSTRUCTION_SET_MAPPER = {x: idx for idx, x in enumerate(COMPILER_INSTRUCTION_SET)}


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
        operator_overlaps = {x[0]: x for x in COMPILER_OPERATORS if (x[0] != x and x[0] in COMPILER_OPERATORS)}

        # do magic
        output = []
        token = ""
        for idx, char in enumerate(code):
            # if char is a spacer
            if char in COMPILER_SPACERS:
                if token:
                    output.append(token)
                    token = ""

            # for non overlapping operators
            elif char in COMPILER_OPERATORS and char not in operator_overlaps:
                if token:
                    output.append(token)
                    token = ""
                output.append(char)
            else:
                token += char

        # output
        return output


def infix_to_rpn(expression: str) -> list[str]:
    """
    Converts an infix math string to reverse polish notation string
    :param expression: expression
    :return: RPN string
    """

    # order of operation
    precedence = {
        "=": 0,
        ">": 1,
        "<": 1,
        "+": 2,
        "-": 2,
        "*": 3,
        "/": 3,
        "**": 4,
    }

    # operator associativity
    associativity = {
        "=": "R",
        ">": "L",
        "<": "L",
        "+": "L",
        "-": "L",
        "*": "L",
        "/": "L",
        "**": "R",
    }

    tokens = code_to_tokens(expression)

    output = []
    stack = []

    for token in tokens:
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


def tokens_to_structs(tokens: list[str]) -> list[list[str]]:
    """
    Converts list of tokens to small structures
    :param tokens: list of tokens
    :return: structs
    """

    tokens = deepcopy(tokens)

    output = []
    stack = []
    while tokens:
        token = tokens.pop(0)

        if token == "\n":
            # dump line to output
            if stack:
                output.append(stack[::])
            stack.clear()
        elif token == "#":
            # skip over the line
            while (_ := tokens.pop(0)) != "\n":
                pass
        else:
            stack.append(token)
    if stack:
        output.append(stack)
    return output


class Compiler:
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
            for nibble in nibbles[::-1][:8-from_left]:
                self.push(f"LDAR {nibble}")
        else:
            for nibble in nibbles[:8-from_right]:
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

        acc = 0    # ACC
        br = 0     # BR
        mr = 0     # MR
        cf = 0     # CF

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
                    elif operand == "PC":
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
        while ptr < len(new_output)-1:
            ptr += 1
            if COMPILER_INSTRUCTION_SET_MAPPER[new_output[ptr][0]] < 4:
                if ptr >= 1 and new_output[ptr-1][0] == new_output[ptr+1][0] == "CA":
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

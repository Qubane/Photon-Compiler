"""
Simple emulator for Photon CPU
"""


class Emulator:
    def __init__(self):
        self.ACC: int = 0
        self.BR: int = 0
        self.MR: int = 0
        self.PC: int = 0

        self.CF: bool = False

        self.memory: list[int] = [0 for _ in range(256)]

    def execute(self, asm: list[list[str]]):
        """
        Executes the assembly instructions
        :param asm: assembly
        """

        instruction_count = 0
        while self.PC < len(asm):
            instruction_count += 1

            # fetch instruction
            if len(asm[self.PC]) == 2:
                instruction, operand = asm[self.PC]
            else:
                instruction = asm[self.PC][0]
                operand = 0

            self.ACC &= 0xFF  # ensure 255 range
            match instruction:
                case "LDAR":
                    self.ACC = (self.ACC << 1) | int(operand)
                case "LDAL":
                    self.ACC = (self.ACC >> 1) | (int(operand) << 7)
                case "MOVC":
                    if operand == "BR" and not self.CF:
                        self.BR = self.ACC
                    elif operand == "MR" and not self.CF:
                        self.MR = self.ACC
                    elif operand == "PC" and not self.CF:
                        self.PC = self.ACC - 1
                case "MOV":
                    self.BR = self.ACC
                case "CA":
                    self.ACC = 0
                case "ADD":
                    self.ACC += self.BR
                    if self.ACC > 255:
                        self.CF = True
                    else:
                        self.CF = False
                case "SUB":
                    self.ACC -= self.BR
                    if self.ACC < 0:
                        self.CF = True
                    else:
                        self.CF = False
                case "AND":
                    self.ACC &= self.BR
                    self.CF = False
                case "OR":
                    self.ACC |= self.BR
                    self.CF = False
                case "XOR":
                    self.ACC ^= self.BR
                    self.CF = False
                case "RD":
                    self.ACC = self.memory[self.MR]
                case "WT":
                    self.memory[self.MR] = self.ACC

            self.PC += 1
        print(f"Done in {instruction_count} instructions")

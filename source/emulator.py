"""
Simple emulator for Photon CPU
"""


from source.classes import *


class Emulator:
    def __init__(self):
        self.ACC: int = 0
        self.BR: int = 0
        self.MR: int = 0
        self.PR: int = 0
        self.CF: bool = False

        self.bit_width: int = 12
        self._max_int: int = 2 ** self.bit_width - 1

        self.max_memory_size = 2**24  # 16 mil addresses
        self.memory: list[int] = [0 for _ in range(min(self.max_memory_size, 2**self.bit_width))]

        self._instruction_mapper = [
            self._asm_lar_0,
            self._asm_lar_1,
            self._asm_lal_0,
            self._asm_lal_1,
            self._asm_movc_br,
            self._asm_movc_mr,
            self._asm_movc_pr,
            self._asm_mov_br,
            self._asm_ca,
            self._asm_add,
            self._asm_sub,
            self._asm_and,
            self._asm_or,
            self._asm_xor,
            self._asm_rd,
            self._asm_wt]

    def _asm_lar_0(self):
        self.ACC <<= 1

    def _asm_lar_1(self):
        self.ACC = (self.ACC << 1) | 1

    def _asm_lal_0(self):
        self.ACC >>= 1

    def _asm_lal_1(self):
        self.ACC = (self.ACC >> 1) | (1 << (self.bit_width - 1))

    def _asm_movc_br(self):
        if not self.CF:
            self.BR = self.ACC

    def _asm_movc_mr(self):
        if not self.CF:
            self.MR = self.ACC

    def _asm_movc_pr(self):
        if not self.CF:
            # print(self.PR, self.PR + (self.ACC - 2**(self.bit_width - 1)) + 1)
            self.PR += self.ACC - 2**(self.bit_width - 1)

    def _asm_mov_br(self):
        self.BR = self.ACC

    def _asm_ca(self):
        self.ACC = 0

    def _asm_add(self):
        self.ACC += self.BR
        if self.ACC > self._max_int:
            self.CF = True
        else:
            self.CF = False

    def _asm_sub(self):
        self.ACC -= self.BR
        if self.ACC < 0:
            self.CF = True
        else:
            self.CF = False

    def _asm_and(self):
        self.ACC &= self.BR
        self.CF = False

    def _asm_or(self):
        self.ACC |= self.BR
        self.CF = False

    def _asm_xor(self):
        self.ACC ^= self.BR
        self.CF = False

    def _asm_rd(self):
        self.ACC = self.memory[self.MR % self.max_memory_size]

    def _asm_wt(self):
        self.memory[self.MR % self.max_memory_size] = self.ACC

    def execute(self, asm: list[PhotonIS]):
        """
        Executes the assembly instructions
        :param asm: assembly
        """

        instruction_count = 0
        while self.PR < len(asm):
            instruction_count += 1

            self.ACC &= self._max_int
            # print(self.PR, asm[self.PR])
            self._instruction_mapper[asm[self.PR].value]()
            self.PR += 1
        print(f"Done in {instruction_count} instructions")
        print(self.memory[:16])

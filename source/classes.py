"""
Class definitions for compiler
"""


from enum import IntEnum


class PhotonIS(IntEnum):
    """
    Photon r.2 Instructions Set
    """

    # Load Accumulator Right
    LAR_0 = 0
    LAR_1 = 1

    # Load Accumulator Left
    LAL_0 = 2
    LAL_1 = 3

    # Move operations (conditional and unconditional)
    MOVC_BR = 4
    MOVC_MR = 5
    MOVC_PR = 6
    MOV_BR = 7

    # Clear
    CA = 8

    # Arithmetic
    ADD = 9
    SUB = 10

    # Boolean
    AND = 11
    OR = 12
    XOR = 13

    # Memory
    RD = 14
    WT = 15

    def __repr__(self):
        if self.value > 8:
            return self.name
        return self.name.replace("_", " ")

    def __str__(self):
        return self.__repr__()


PHOTON_INSTRUCTION_SET = {PhotonIS(x).name.split("_")[0]: x for x in range(16)}

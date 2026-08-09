"""
Class definitions for compiler
"""


from enum import IntEnum, auto


class PhotonIS(IntEnum):
    """
    Photon r.2 Instructions Set
    """

    # Load Accumulator Right
    LAR_0 = auto()
    LAR_1 = auto()

    # Load Accumulator Left
    LAL_0 = auto()
    LAL_1 = auto()

    # Move operations (conditional and unconditional)
    MOVC_BR = auto()
    MOVC_MR = auto()
    MOVC_PR = auto()
    MOV_BR = auto()

    # Clear
    CA = auto()

    # Arithmetic
    ADD = auto()
    SUB = auto()

    # Boolean
    AND = auto()
    OR = auto()
    XOR = auto()

    # Memory
    RD = auto()
    WT = auto()

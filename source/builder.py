"""
Builds compiled code to bytecode and to scrap mechanic blueprints
"""


import os
import json
from source.classes import *


# make blueprints directory
if not os.path.isdir("blueprints"):
    os.mkdir("blueprints")


class AssemblyBuilder:
    """
    Builds assembly code to bytecode
    """

    instruction_4_lut = {
        "lda": 0,
        "movc": 1,
        "mov": 1,

        "ca": 8,
        "add": 9,
        "sub": 10,
        "and": 11,
        "or": 12,
        "xor": 13,
        "rd": 14,
        "wt": 15}

    @classmethod
    def build(cls, code: list[TokenLine]) -> list[int]:
        """
        Builds instructions to bytecode
        :param code: list of instructions
        :return: bytecode
        """

        # go through instructions and append the converted bytecode
        converted_bytecode = []
        for token_line in code:
            instruction = token_line[0].lower()

            # instruction with args
            if instruction in {"lda", "movc", "mov"}:
                bytecode = cls.instruction_4_lut[instruction] << 2
                bytecode += token_line[1]

            # other instructions
            elif instruction in cls.instruction_4_lut:
                bytecode = cls.instruction_4_lut[instruction]

            # undefined instructions
            else:
                raise NotImplementedError

            converted_bytecode.append(bytecode)

        # return bytecode
        return converted_bytecode


class BlueprintBuilder:
    """
    Blueprint builder class
    """

    card_block_uuid: str = "628b2d61-5ceb-43e9-8334-a4135566df7a"
    color_4_lut: list[str] = [
        "EEEEEE", "7F7F7F", "4A4A4A", "222222",
        "F5F071", "E2DB13", "817C00", "323000",
        "CBF66F", "A0EA00", "577D07", "375000",
        "68FF88", "19E753", "0E8031", "064023"]

    @classmethod
    def make_block(cls, pos: tuple[int, int, int], color: str) -> dict:
        """
        Makes a blueprint block
        :param pos: block integer position
        :param color: block color
        :return: block
        """

        return {
            "bounds": {"x": 1, "y": 1, "z": 1},
            "color": color,
            "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
            "shapeId": cls.card_block_uuid,
            "xaxis": 1,
            "zaxis": 3}

    @staticmethod
    def make_raw_blueprint(blueprint: list, name: str):
        """
        Makes raw blueprint for scrap mechanic
        :param blueprint: blueprint data
        :param name: name for the blueprint
        """

        # dump blueprint data
        blueprint = {"bodies": [{"childs": blueprint}], "version": 4}
        with open(f"blueprints/blueprint.json", "w") as file:
            json.dump(blueprint, file)

    @classmethod
    def make_bw4_card(cls, code: list[int]) -> list:
        """
        Make black&white 4 bit wide instruction program card.
        Used by Photon Mini r2
        :param code: list of instructions
        :return: blueprint data
        """

        blocks = []
        for idx, bytecode in enumerate(code):
            for bit in range(4):
                bit_mask = 1 << bit
                if (bytecode & bit_mask) > 0:
                    color = cls.color_4_lut[0]
                else:
                    color = cls.color_4_lut[3]
                blocks.append(cls.make_block((4 - bit, idx, 0), color))
        return blocks

    @classmethod
    def make_c4_card(cls, code: list[int]) -> list:
        """
        Makes colored 4 bits per color; 4 bit wide instruction program card.
        :param code: list of instructions
        :return: blueprint data
        """

        blocks = []
        for idx in range(len(code) // 4):
            instructions = code[idx * 4:idx * 4 + 4]
            for bit in range(4):
                color_value = (instructions[0] & (1 << bit)) >> bit
                color_value += ((instructions[1] & (1 << bit)) >> bit) << 1 if len(instructions) > 1 else 0
                color_value += ((instructions[2] & (1 << bit)) >> bit) << 2 if len(instructions) > 2 else 0
                color_value += ((instructions[3] & (1 << bit)) >> bit) << 3 if len(instructions) > 3 else 0

                blocks.append(cls.make_block((4 - bit, idx, 0), cls.color_4_lut[color_value]))
        return blocks

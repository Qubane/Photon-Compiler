"""
Builds compiled code to bytecode and to scrap mechanic blueprints
"""


import os
import uuid
import json
from PIL import Image
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

        # make uuid
        blueprint_uuid = uuid.uuid4()

        # make blueprint directory
        directory_path = f"blueprints/{blueprint_uuid}"
        os.mkdir(directory_path)

        # make "preview" icon
        Image.effect_noise((128, 128), 1).save(f"{directory_path}/icon.png")

        # make description
        description = {
            "description": "bytecode generated via Photon Compiler",
            "localId": f"{blueprint_uuid}",
            "name": f"{name}",
            "type": "blueprint",
            "version": 0}

        # dump description
        with open(f"{directory_path}/description.json", "w") as file:
            json.dump(description, file, indent=4)

        # dump blueprint data
        blueprint = {"bodies": [{"childs": blueprint}], "version": 4}
        with open(f"{directory_path}/blueprint.json", "w") as file:
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
                    color = "EEEEEE"
                else:
                    color = "222222"
                blocks.append(cls.make_block((idx, bit, 0), color))
        return blocks

    @classmethod
    def make_c4_card(cls, code: list[int]) -> list:
        """
        Makes colored 4 bits per color; 4 bit wide instruction program card.
        :param code: list of instructions
        :return: blueprint data
        """

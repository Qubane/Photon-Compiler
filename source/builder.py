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


class BlueprintBuilder:
    """
    Blueprint builder class
    """

    @staticmethod
    def make_raw_blueprint(blueprint: dict, name: str):
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
        with open(f"{directory_path}/blueprint.json", "w") as file:
            json.dump(blueprint, file)

    @staticmethod
    def make_bw4_card(code: list[TokenLine]) -> dict:
        """
        Make black&white 4 bit wide instruction program card.
        Used by Photon Mini r2
        :param code: list of instructions
        :return: blueprint data
        """

    @staticmethod
    def make_c4_card(code: list[TokenLine]) -> dict:
        """
        Makes colored 4 bits per color; 4 bit wide instruction program card.
        :param code: list of instructions
        :return: blueprint data
        """

"""
Main application file
"""


import argparse
from source.parser import *
from source.compiler import *
from source.builder import *


class Application:
    """
    Application class
    """

    def __init__(self):
        self.parse_input_file: str = ""
        self.parse_output_file: str = ""
        self.parse_blueprint_type: str = ""

    def parse_cli(self):
        """
        Parses CLI
        """

        # define parser
        parser = argparse.ArgumentParser(
            prog="Photon Compiler",
            description="Compiler for Scrap Mechanic CPU")

        # add arguments
        parser.add_argument(
            "-i", "--input",
            help="source input file",
            required=True)
        parser.add_argument(
            "-o", "--output",
            help="bytecode output file")
        parser.add_argument(
            "-t", "--type",
            help="blueprint output type",
            choices=["bw", "c4"],
            default="bw")

        # parse arguments
        args = parser.parse_args()

        self.parse_input_file = args.input
        self.parse_output_file = args.output
        if args.output is None:
            self.parse_output_file = self.parse_input_file + ".bin"
        self.parse_blueprint_type = args.type

    def run(self):
        """
        Runs the application
        """

        # parse arguments
        self.parse_cli()

        # read source file
        with open(self.parse_input_file, "r", encoding="utf-8") as file:
            source_code = file.read()

        # parse source file
        parsed_code = Parser.parse(source_code)

        # compile source code
        compiler = Compiler()
        compiled_code = compiler.compile(parsed_code)

        # print out the result
        for idx, token_line in enumerate(compiled_code):
            print(f"{idx: >3}", " ".join(f"{x: <4}" for x in token_line))

        # write to blueprint
        bytecode = AssemblyBuilder.build(compiled_code)
        if self.parse_blueprint_type == "bw":
            blueprint = BlueprintBuilder.make_bw4_card(bytecode)
        elif self.parse_blueprint_type == "c4":
            blueprint = BlueprintBuilder.make_c4_card(bytecode)
        else:
            raise NotImplementedError
        BlueprintBuilder.make_raw_blueprint(blueprint, "test program")

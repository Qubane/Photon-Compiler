"""
Main application file
"""


import argparse


class Application:
    """
    Application class
    """

    def __init__(self):
        self.parse_input_file: str = ""
        self.parse_output_file: str = ""

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

        # parse arguments
        args = parser.parse_args()

        self.parse_input_file = args.input
        self.parse_output_file = args.output
        if args.output is None:
            self.parse_output_file = self.parse_input_file + ".bin"

    def run(self):
        """
        Runs the application
        """

        self.parse_cli()

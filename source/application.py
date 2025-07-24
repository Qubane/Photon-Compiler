"""
Main application file
"""


import argparse


class Application:
    """
    Application class
    """

    def __init__(self):
        ...

    def parse_cli(self):
        """
        Parses CLI
        """

        parser = argparse.ArgumentParser(
            prog="Photon Compiler",
            description="Compiler for Scrap Mechanic CPU")

    def run(self):
        """
        Runs the application
        """

        self.parse_cli()

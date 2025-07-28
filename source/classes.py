"""
Some helper classes
"""


class TokenLine(list):
    """
    Container for multiple tokens
    """

    def __init__(self, *args, reference_line: int = -1):
        super().__init__(*args)

        self.reference_line: int = reference_line

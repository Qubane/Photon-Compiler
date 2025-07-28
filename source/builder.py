"""
Builds compiled code to bytecode and to scrap mechanic blueprints
"""


import os


# make blueprints directory
if not os.path.isdir("blueprints"):
    os.mkdir("blueprints")

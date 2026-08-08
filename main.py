import json
from source.compiler import *
from source.emulator import *


test = """
a=10
b = 40
c = ((b + 2) - a)

d = a

# random if check for no reason
if a + b > c
    c = a + b - 1
end

for i in range(4)
    a = a + b
end

"""

test2 = """
a = 0
b = 10

if a > b
    b = a - 1
end
"""


def main():
    tokens = code_to_tokens(test2)
    tok_struct = tokens_to_structs(tokens)

    compiler = Compiler()
    asm = compiler.compile(tok_struct)
    print(tokens)
    print(tok_struct)
    print(asm)

    emulator = Emulator()
    emulator.execute(asm)


if __name__ == '__main__':
    main()

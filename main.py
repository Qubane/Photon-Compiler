import json
from source.compiler import *
from source.emulator import *


test1 = """
a=10
b = 40
c = ((b + 2) - a)

d = a

e = 1 << 2
f = (a << 1) | b

# random if check for no reason
if a + b > c
    c = a + b - 1
end

for i in range(4)
    a = a + b
end

"""

test2 = """
a = 9
b = 10

if a > b
    b = 1
else
    b = 2
end

"""

test3 = """
a = 1 << 2
"""


def main():
    tokens = Lexer.code_to_tokens(test2)
    structs = Lexer.tokens_to_struct(tokens)

    print(tokens)
    print(structs)

    compiler = Compiler()
    compiled = compiler.compile(structs)

    print("\n".join(f"{idx: >{len(str(len(compiled)))}} {x}" for idx, x in enumerate(compiled)))

    emulator = Emulator()
    emulator.execute(compiled)


if __name__ == '__main__':
    main()

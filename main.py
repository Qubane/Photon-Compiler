import json
from source.compiler import *
from source.emulator import *


test1 = """
# if statement test
a = 9
b = 10

if a > b
    b = 1
else
    b = 2
end

"""

test2 = """
# while statement test
a = 0

while a < 10
    a = a + 1
end
"""

test3 = """
# fibonacci sequence
i = 0

a = 0
b = 1

while i != 10
    b = a + b
    a = b - a
    
    i = i + 1
end
"""

test4 = """
# nested statements

y = 0
while y != 2
    x = 0
    while x != 2
        x = x + 1
    end
    y = y + 1
end
"""


def main():
    tokens = Lexer.code_to_tokens(test4)
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

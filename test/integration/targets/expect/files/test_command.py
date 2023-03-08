from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

try:
    input_function = raw_input
except NameError:
    input_function = input


# function used to read a single char from the stdin without
# waiting for the "\n". This was done to avoid external dependencies.
def getChar():
    # check which function we should use
    if "_func" not in getChar.__dict__:
        try:
            # for Windows-based systems
            import msvcrt

            getChar._func = msvcrt.getch

        except ImportError:
            # otherwise
            import tty
            import sys
            import termios  # raises ImportError if unsupported

            def _ttyRead():
                fd = sys.stdin.fileno()
                oldSettings = termios.tcgetattr(fd)

                try:
                    tty.setcbreak(fd)
                    answer = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

                return answer

            getChar._func = _ttyRead
    return getChar._func()


# read all prompts
all_prompts = sys.argv[1:] or ['foo']

# get only standard prompts, those not starting with 'raw_'
standard_prompts = [prompt for prompt in all_prompts if not prompt.startswith("raw_")]

# get only raw prompts, we do not use a set transformation to preserve the order
raw_prompts = [prompt for prompt in all_prompts if prompt not in standard_prompts]

# latin1 encoded bytes
# to ensure pexpect doesn't have any encoding errors
data = b'premi\xe8re is first\npremie?re is slightly different\n????????? is Cyrillic\n? am Deseret\n'

try:
    sys.stdout.buffer.write(data)
except AttributeError:
    sys.stdout.write(data)
print()

# loop over standard prompts first
for prompt in standard_prompts:
    user_input = input_function(prompt)
    print(user_input)

# loop over raw prompts
for raw_prompt in raw_prompts:
    sys.stdout.write(raw_prompt)
    sys.stdout.flush()
    user_char_input = getChar()
    print()
    print(user_char_input)

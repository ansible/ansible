from __future__ import annotations

import sys

try:
    input_function = raw_input
except NameError:
    input_function = input

prompts = sys.argv[1:] or ['foo']

# latin1 encoded bytes
# to ensure pexpect doesn't have any encoding errors
data = b'premi\xe8re is first\npremie?re is slightly different\n????????? is Cyrillic\n? am Deseret\n'

try:
    sys.stdout.buffer.write(data)
except AttributeError:
    sys.stdout.write(data)
print()

for prompt in prompts:
    user_input = input_function(prompt)
    print(user_input)

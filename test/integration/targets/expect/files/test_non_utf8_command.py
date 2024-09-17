from __future__ import annotations

import sys

prompts = sys.argv[1:] or ['foo']

# latin1 encoded bytes
# to ensure pexpect doesn't have any encoding errors
data = b'premi\xe8re is first\npremie?re is slightly different\n????????? is Cyrillic\n? am Deseret\n'

sys.stdout.buffer.write(data)
print()

for prompt in prompts:
    user_input = input(prompt)
    print(user_input)

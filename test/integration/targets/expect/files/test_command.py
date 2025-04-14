from __future__ import annotations

import sys

prompts = sys.argv[1:] or ['foo']

# UTF8 encoded bytes
# to ensure pexpect doesn't have any encoding errors
data = 'line one 汉语\nline two\nline three\nline four\n'.encode()

sys.stdout.buffer.write(data)
print()

for prompt in prompts:
    user_input = input(prompt)
    print(user_input)

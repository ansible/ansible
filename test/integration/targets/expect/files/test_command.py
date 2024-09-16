from __future__ import annotations

import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--latin1', action='store_true')
parser.add_argument('prompts', nargs='*')
args = parser.parse_args()

prompts = args.prompts or ['foo']


def tty_prompt(prompt):
    fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
    with os.fdopen(fd, 'w') as stream:
        stream.write(prompt)
        stream.close()

    response = input()
    return response


# latin1 encoded bytes
# to ensure pexpect doesn't have any encoding errors
data = b'premi\xe8re is first\npremie?re is slightly different\n????????? is Cyrillic\n? am Deseret\n'

if args.latin1:
    try:
        sys.stdout.buffer.write(data)
    except AttributeError:
        sys.stdout.write(data)
    print()

for prompt in prompts:
    user_input = tty_prompt(prompt)
    print(user_input)

import sys

from ansible.module_utils.six.moves import input


prompts = sys.argv[1:] or ['foo']

for prompt in prompts:
    user_input = input(prompt)
    print(user_input)

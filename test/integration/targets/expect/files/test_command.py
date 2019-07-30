import sys

try:
    input_function = raw_input
except NameError:
    input_function = input

prompts = sys.argv[1:] or ['foo']

for prompt in prompts:
    user_input = input_function(prompt)
    print(user_input)

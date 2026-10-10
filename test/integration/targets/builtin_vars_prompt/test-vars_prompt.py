#!/usr/bin/env python

from __future__ import annotations

import io
import os
import pexpect
import sys
import subprocess


env_vars = {
    'ANSIBLE_ROLES_PATH': './roles',
    'ANSIBLE_NOCOLOR': 'True',
    'ANSIBLE_RETRY_FILES_ENABLED': 'False',
}


def run_test(playbook, test_spec, args=None, timeout=10, env=None, forbidden_values=(), expected_status=0):

    if not env:
        env = os.environ.copy()
    env.update(env_vars)

    if not args:
        args = sys.argv[1:]

    vars_prompt_test = pexpect.spawn(
        'ansible-playbook',
        args=[playbook] + args,
        timeout=timeout,
        env=env,
    )

    transcript = io.BytesIO()
    vars_prompt_test.logfile_read = transcript
    for item in test_spec[0]:
        vars_prompt_test.expect(item[0])
        if item[1]:
            vars_prompt_test.send(item[1])
    vars_prompt_test.expect(test_spec[1])
    vars_prompt_test.expect(pexpect.EOF)
    vars_prompt_test.close()
    output = transcript.getvalue()
    sys.stdout.buffer.write(output)
    assert vars_prompt_test.exitstatus == expected_status
    for value in forbidden_values:
        assert value.encode() not in output


# These are the tests to run. Each test is a playbook and a test_spec.
#
# The test_spec is a list with two elements.
#
# The first element is a list of two element tuples. The first is the regexp to look
# for in the output, the second is the line to send.
#
# The last element is the last string of text to look for in the output.
#
tests = [
    # Basic vars_prompt
    {'playbook': 'vars_prompt-1.yml',
     'test_spec': [
        [('input:', 'some input\r')],
         r'"input": "\$REDACTED\$"']},

    # Custom prompt
    {'playbook': 'vars_prompt-2.yml',
     'test_spec': [
         [('Enter some input:', 'some more input\r')],
         r'"input": "\$REDACTED\$"']},

    # Test confirm, both correct and incorrect
    {'playbook': 'vars_prompt-3.yml',
     'test_spec': [
         [('input:', 'confirm me\r'),
          ('confirm input:', 'confirm me\r')],
         r'"input": "\$REDACTED\$"']},

    {'playbook': 'vars_prompt-3.yml',
     'test_spec': [
         [('input:', 'confirm me\r'),
          ('confirm input:', 'incorrect\r'),
          (r'\*\*\*\*\* VALUES ENTERED DO NOT MATCH \*\*\*\*', ''),
          ('input:', 'confirm me\r'),
          ('confirm input:', 'confirm me\r')],
         r'"input": "\$REDACTED\$"']},

    # Test private
    {'playbook': 'vars_prompt-4.yml',
     'test_spec': [
         [('not_secret', 'this is displayed\r'),
          ('this is displayed', '')],
         '"not_secret": "this is displayed"']},

    # Test hashing
    {'playbook': 'vars_prompt-5.yml',
     'test_spec': [
         [('password', 'Scenic-Improving-Payphone\r'),
          ('confirm password', 'Scenic-Improving-Payphone\r')],
         r'"msg": "\$REDACTED\$ \$6\$']},

    # Test variables in prompt field
    # https://github.com/ansible/ansible/issues/32723
    {'playbook': 'vars_prompt-6.yml',
     'test_spec': [
         [('prompt from variable:', 'input\r')],
         '']},

    # Test play vars coming from vars_prompt
    # https://github.com/ansible/ansible/issues/37984
    {'playbook': 'vars_prompt-7.yml',
     'test_spec': [
         [('prompting for host:', 'testhost\r')],
         r'testhost.*ok=1']},

    # Test play unsafe toggle
    {'playbook': 'unsafe.yml',
     'test_spec': [
         [('prompting for variable:', '{{whole}}\r')],
         r'testhost.*ok=2']},

    # Retry an invalid default and a partial match, even when play vars define the name.
    {'playbook': 'validate.yml',
     'test_spec': [
         [('Enter number', '\r'),
          ('Invalid input', ''),
          ('Enter number', 'prefix123suffix\r'),
          ('Invalid input', ''),
          ('Enter number', '123\r')],
         'All assertions passed']},

    # Validate confirmed plaintext, then hash it.
    {'playbook': 'validate-private.yml',
     'forbidden_values': ['invalid-secret'],
     'test_spec': [
         [('Enter password:', 'invalid-secret\r'),
          ('confirm Enter password:', 'invalid-secret\r'),
          ('Invalid input', ''),
          ('Enter password:', '123\r'),
          ('confirm Enter password:', '456\r'),
          (r'\*\*\*\*\* VALUES ENTERED DO NOT MATCH', ''),
          ('Enter password:', '123\r'),
          ('confirm Enter password:', '123\r')],
         'testhost.*ok=1']},

    # Test unsupported keys
    {'playbook': 'unsupported.yml',
     'expected_status': 4,
     'test_spec': [
         [],
         "Invalid vars_prompt data structure, found unsupported key 'when'"]},
]

for t in tests:
    run_test(**t)


def run_noninteractive(args: list[str], expected_status: int) -> str:
    """Exercise skipped prompts and defaults without a terminal or an unbounded wait."""
    env = os.environ.copy()
    env.update(env_vars)
    result = subprocess.run(
        ['ansible-playbook', 'validate.yml', *sys.argv[1:], *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=30, env=env, check=False,
    )
    sys.stdout.write(result.stdout)
    assert result.returncode == expected_status, result.stdout
    return result.stdout


# Extra vars continue to bypass prompt validation, including a value outside the pattern.
assert 'All assertions passed' in run_noninteractive(['-e', 'number=123'], 0)
output = run_noninteractive(['-e', 'number=outside-pattern'], 2)
assert 'Assertion failed' in output
assert 'Invalid input' not in output
assert 'non-interactive mode' not in output

# Listing and syntax checks must not attempt input or reject the unused default.
for option in ['--syntax-check', '--list-hosts', '--list-tasks', '--list-tags']:
    output = run_noninteractive([option], 0)
    assert 'Not prompting' not in output
    assert 'Invalid input' not in output

# An invalid default must fail promptly when no interactive input is possible.
output = run_noninteractive([], 1)
assert 'non-interactive mode' in output
assert 'Invalid input' not in output


# Configuration errors must be reported even during a syntax check.
output = run_noninteractive(['--syntax-check', '-e', 'number_pattern=['], 1)
assert 'Invalid regular expression in vars_prompt validate' in output
output = run_noninteractive(['--syntax-check', '-e', '{"number_pattern": 42}'], 1)
assert 'vars_prompt validate option must be a string' in output

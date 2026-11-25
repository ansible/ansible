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
    'ANSIBLE_PROMPT_TEST_VALUE': 'abc',
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
    try:
        for item in test_spec[0]:
            vars_prompt_test.expect(item[0])
            if item[1]:
                vars_prompt_test.send(item[1])
        vars_prompt_test.expect(test_spec[1])
        vars_prompt_test.expect(pexpect.EOF)
    finally:
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
          ('INVALID INPUT', ''),
          ('Enter number', 'prefix123suffix\r'),
          ('INVALID INPUT', ''),
          ('Enter number', '123\r')],
         'All assertions passed']},

    # Validate confirmed plaintext, then hash it.
    {'playbook': 'validate-private.yml',
     'forbidden_values': ['invalid-secret'],
     'test_spec': [
         [('Enter password:', 'invalid-secret\r'),
          ('confirm Enter password:', 'invalid-secret\r'),
          ('INVALID INPUT', ''),
          ('Enter password:', '123\r'),
          ('confirm Enter password:', '456\r'),
          (r'\*\*\*\*\* VALUES ENTERED DO NOT MATCH', ''),
          ('Enter password:', '123\r'),
          ('confirm Enter password:', '123\r')],
         'testhost.*ok=1']},

    # Membership uses earlier prompt input and play variables without a regex.
    {'playbook': 'validate-jinja.yml',
     'test_spec': [
         [('Enter environment:', 'unknown\r'),
          ('INVALID INPUT', ''),
          ('Enter environment:', 'prod\r'),
          ('Confirm environment:', 'staging\r'),
          ('INVALID INPUT', ''),
          ('Confirm environment:', 'prod\r'),
          ('Enter URL:', 'http://example.org\r'),
          ('INVALID INPUT', ''),
          ('Enter URL:', 'https://example.org\r'),
          ('Enter code:', 'long\r'),
          ('INVALID INPUT', ''),
          ('Enter code:', 'abc\r')],
         'All assertions passed']},

    # Interrupts from the Display input API retain the CLI's normal exit behavior.
    {'playbook': 'validate.yml',
     'expected_status': 99,
     'test_spec': [
         [('Enter number', '\x03')],
         'User interrupted execution']},

    # Test unsupported keys
    {'playbook': 'unsupported.yml',
     'expected_status': 4,
     'test_spec': [
         [],
         "Invalid vars_prompt data structure, found unsupported key 'when'"]},
]

for t in tests:
    run_test(**t)


def run_noninteractive(args: list[str], expected_status: int, playbook: str = 'validate.yml') -> str:
    """Exercise skipped prompts and defaults without a terminal or an unbounded wait."""
    env = os.environ.copy()
    env.update(env_vars)
    result = subprocess.run(
        ['ansible-playbook', playbook, *sys.argv[1:], *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=30, env=env, check=False,
    )
    sys.stdout.write(result.stdout)
    assert result.returncode == expected_status
    return result.stdout


# Extra vars continue to bypass prompt validation, including a value outside the pattern.
assert 'All assertions passed' in run_noninteractive(['-e', 'number=123'], 0)
output = run_noninteractive(['-e', 'number=outside-pattern'], 2)
assert 'Assertion failed' in output
assert 'INVALID INPUT' not in output
assert 'non-interactive mode' not in output

# Listing and syntax checks must not attempt input or reject the unused default.
for option in ['--syntax-check', '--list-hosts', '--list-tasks', '--list-tags']:
    output = run_noninteractive([option], 0)
    assert 'Not prompting' not in output
    assert 'INVALID INPUT' not in output

# An invalid default must fail promptly when no interactive input is possible.
output = run_noninteractive([], 1)
assert 'non-interactive mode' in output
assert 'INVALID INPUT' not in output


# Both prompt paths hash accepted defaults once, after any validation.
output = run_noninteractive([], 0, 'hash-defaults.yml')
assert 'All assertions passed' in output
assert 'default-secret' not in output


# A None default is accepted or rejected by the expression, not by an implicit guard.
assert 'All assertions passed' in run_noninteractive([], 0, 'validate-none-default.yml')
output = run_noninteractive(['-e', '{"accept_missing": false}'], 1, 'validate-none-default.yml')
assert 'non-interactive mode' in output
assert 'Error evaluating vars_prompt validation' not in output


# Expressions refer to play variables; an invalid regex is an evaluation error at runtime.
output = run_noninteractive(['-e', 'number_pattern=['], 1)
assert 'non-interactive mode' not in output
assert 'Error evaluating vars_prompt validation' in output


# Unused validation expressions are not evaluated by syntax checks or listing commands.
for playbook in ['validate-invalid-expression.yml', 'validate-invalid-type.yml']:
    for option in ['--syntax-check', '--list-hosts', '--list-tasks', '--list-tags']:
        output = run_noninteractive([option], 0, playbook)
        assert 'Error evaluating vars_prompt validation' not in output
    output = run_noninteractive(['-e', 'number=123'], 0, playbook)
    assert 'Error evaluating vars_prompt validation' not in output

    # The same invalid expression must still fail when a candidate is evaluated.
    output = run_noninteractive([], 1, playbook)
    assert 'Error evaluating vars_prompt validation' in output

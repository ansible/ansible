#!/usr/bin/env python

import os
import pexpect
import sys
import termios

from ansible.module_utils.six import PY2

args = sys.argv[1:]

env_vars = {
    'ANSIBLE_ROLES_PATH': './roles',
    'ANSIBLE_NOCOLOR': 'True',
    'ANSIBLE_RETRY_FILES_ENABLED': 'False'
}

try:
    backspace = termios.tcgetattr(sys.stdin.fileno())[6][termios.VERASE]
except Exception:
    backspace = b'\x7f'

if PY2:
    log_buffer = sys.stdout
else:
    log_buffer = sys.stdout.buffer

os.environ.update(env_vars)

# -- Plain pause -- #
playbook = 'pause-1.yml'

# Case 1 - Contiune with enter
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Press enter to continue, Ctrl\+C to interrupt:')
pause_test.send('\r')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 2 - Continue with C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Press enter to continue, Ctrl\+C to interrupt:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('C')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 3 - Abort with A
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Press enter to continue, Ctrl\+C to interrupt:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Custom Prompt -- #
playbook = 'pause-2.yml'

# Case 1 - Contiune with enter
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Custom prompt:')
pause_test.send('\r')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 2 - Contiune with C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Custom prompt:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('C')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 3 - Abort with A
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Custom prompt:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Pause for N seconds -- #

playbook = 'pause-3.yml'

# Case 1 - Wait for task to continue after timeout
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()

# Case 2 - Contiune with Ctrl + C, C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.send('\x03')
pause_test.send('C')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 3 - Abort with Ctrl + C, A
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.send('\x03')
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Pause for N seconds with custom prompt -- #

playbook = 'pause-4.yml'

# Case 1 - Wait for task to continue after timeout
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()

# Case 2 - Contiune with Ctrl + C, C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.send('\x03')
pause_test.send('C')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Case 3 - Abort with Ctrl + C, A
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.send('\x03')
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Enter input and ensure it's caputered, echoed, and can be edited -- #

playbook = 'pause-5.yml'

pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = log_buffer
pause_test.expect(r'Enter some text:')
pause_test.sendline('hello there')
pause_test.expect(r'Enter some text to edit:')
pause_test.send('hello there')
pause_test.send(backspace * 4)
pause_test.send('ommy boy\r')
pause_test.expect(r'Enter some text \(output is hidden\):')
pause_test.sendline('supersecretpancakes')
pause_test.expect(pexpect.EOF)
pause_test.close()

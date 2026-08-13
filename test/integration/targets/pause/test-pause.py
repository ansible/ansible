#!/usr/bin/env python

from __future__ import annotations

import os
import pexpect
import sys
import termios


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

os.environ.update(env_vars)

# -- Plain pause -- #
playbook = 'pause-1.yml'

# Case 1 - Continue with enter
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
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

pause_test.logfile = sys.stdout.buffer
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

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Press enter to continue, Ctrl\+C to interrupt:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Custom Prompt -- #
playbook = 'pause-2.yml'

# Case 1 - Continue with enter
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Custom prompt:')
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

pause_test.logfile = sys.stdout.buffer
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

pause_test.logfile = sys.stdout.buffer
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

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()

# Case 2 - Continue with Ctrl + C, C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.send('\n')  # test newline does not stop the prompt - waiting for a timeout or ctrl+C
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
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

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
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

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()

# Case 2 - Continue with Ctrl + C, C
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
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

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Pausing for \d+ seconds')
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.expect(r"Waiting for two seconds:")
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()

# -- Enter input and ensure it's captured, echoed, and can be edited -- #

playbook = 'pause-5.yml'

pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter some text:')
pause_test.send('hello there')
pause_test.send('\r')
pause_test.expect(r'Enter some text to edit:')
pause_test.send('hello there')
pause_test.send(backspace * 4)
pause_test.send('ommy boy')
pause_test.send('\r')
pause_test.expect(r'Enter some text \(output is hidden\):')
pause_test.send('supersecretpancakes')
pause_test.send('\r')
pause_test.expect(pexpect.EOF)
pause_test.close()

# Test input is not returned if a timeout is given

playbook = 'pause-6.yml'

pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Wait for three seconds:')
pause_test.send('ignored user input')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()


# Test that enter presses may not continue the play when a timeout is set.

pause_test = pexpect.spawn(
    'ansible-playbook',
    args=["pause-3.yml"] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r"\(ctrl\+C then 'C' = continue early, ctrl\+C then 'A' = abort\)")
pause_test.send('\r')
pause_test.expect(pexpect.EOF)
pause_test.close()


# -- timeout_seconds: timeout fires with no input (timed_out=True) --

playbook = 'pause-8.yml'

# Case 1 - Wait for the 2-second deadline to expire (send nothing)
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=15,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter a value or wait for timeout:')
# Do not send any input; let the 2-second timeout fire naturally
pause_test.expect('Task after timeout pause', timeout=15)
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus == 0


# -- timeout_seconds: user answers before expiry (timed_out=False) --

playbook = 'pause-7.yml'

# Case 1 - User sends input before the 30-second deadline
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=15,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter a value with timeout:')
pause_test.send('hello timeout')
pause_test.send('\r')
pause_test.expect('Task after pause', timeout=10)
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus == 0


# -- timeout_seconds: user presses Enter immediately (empty input, timed_out=False) --

playbook = 'pause-9.yml'

# Case 1 - User presses Enter right away; this must NOT set timed_out=True
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Press Enter to continue:')
pause_test.send('\r')
pause_test.expect('Task after enter pause', timeout=10)
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus == 0


# -- timeout_seconds + timeout_action=abort: abort on expiry --

playbook = 'pause-10.yml'

# Case 1 - Let the 2-second deadline fire; the ignored error is caught and asserted in the playbook.
# ignore_errors: yes on the pause task catches the AnsibleError raised by the action plugin,
# allowing the subsequent assert and debug tasks to run and the play to exit 0.
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=[playbook] + args,
    timeout=15,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter a value or the play will abort:')
# Do not send any input; let the timeout fire
pause_test.expect('Task after abort pause', timeout=15)
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus == 0


# -- timeout_seconds: Ctrl+C then Continue --

# Case 1 - Ctrl+C during timeout_seconds prompt, then press C to continue
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=['pause-11.yml'] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter a value with timeout:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('C')
pause_test.expect('Task after pause')
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus == 0


# Case 2 - Ctrl+C during timeout_seconds prompt, then press A to abort
pause_test = pexpect.spawn(
    'ansible-playbook',
    args=['pause-11.yml'] + args,
    timeout=10,
    env=os.environ
)

pause_test.logfile = sys.stdout.buffer
pause_test.expect(r'Enter a value with timeout:')
pause_test.send('\x03')
pause_test.expect("Press 'C' to continue the play or 'A' to abort")
pause_test.send('A')
pause_test.expect('user requested abort!')
pause_test.expect(pexpect.EOF)
pause_test.close()
assert pause_test.exitstatus != 0

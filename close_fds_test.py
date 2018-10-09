#!/usr/bin/python

import datetime
import os
import select
import subprocess


def _read_from_pipes(rpipes, rfds, file_descriptor):
    data = b''
    if file_descriptor in rfds:
        data = os.read(file_descriptor.fileno(), 9000)
        if data == b'':
            rpipes.remove(file_descriptor)

    return data


def run_command(args, cwd=None):
    args = [x for x in args if x is not None]
    kwargs = dict(
        close_fds=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # store the pwd
    prev_dir = os.getcwd()

    # make sure we're in the right working directory
    if cwd and os.path.isdir(cwd):
        cwd = os.path.abspath(os.path.expanduser(cwd))
        kwargs['cwd'] = cwd
        os.chdir(cwd)

    start_time = datetime.datetime.now()
    cmd = subprocess.Popen(args, **kwargs)

    # the communication logic here is essentially taken from that
    # of the _communicate() function in ssh.py

    stdout = b''
    stderr = b''
    rpipes = [cmd.stdout, cmd.stderr]

    while True:
        rfds, wfds, efds = select.select(rpipes, [], rpipes, 1)
        stdout += _read_from_pipes(rpipes, rfds, cmd.stdout)
        stderr += _read_from_pipes(rpipes, rfds, cmd.stderr)

        # only break out if no pipes are left to read or
        # the pipes are completely read and
        # the process is terminated
        if (not rpipes or not rfds) and cmd.poll() is not None:
            break
        # No pipes are left to read but process is not yet terminated
        # Only then it is safe to wait for the process to be finished
        # NOTE: Actually cmd.poll() is always None here if rpipes is empty
        elif not rpipes and cmd.poll() is None:
            cmd.wait()
            # The process is terminated. Since no pipes to read from are
            # left, there is no need to call select() again.
            break

    cmd.stdout.close()
    cmd.stderr.close()

    rc = cmd.returncode
    total_time = datetime.datetime.now() - start_time
    elapsed_time = (total_time.microseconds + 0.0 + (
                total_time.seconds + total_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    print("(%s) - %s" % (elapsed_time, " ".join(args)))

    # reset the pwd
    os.chdir(prev_dir)
    return (rc, stdout, stderr)


def run_command2(args):
    args = [x for x in args if x is not None]
    start_time = datetime.datetime.now()
    res = subprocess.call(args)
    total_time = datetime.datetime.now() - start_time
    elapsed_time = (total_time.microseconds + 0.0 + (
                total_time.seconds + total_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    print("(%s) - %s" % (elapsed_time, " ".join(args)))
    return res


def run_command3(args):
    args = [x for x in args if x is not None]
    start_time = datetime.datetime.now()

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout_value = proc.communicate()[0]

    total_time = datetime.datetime.now() - start_time
    elapsed_time = (total_time.microseconds + 0.0 + (
                total_time.seconds + total_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    print("(%s) - %s" % (elapsed_time, " ".join(args)))
    return stdout_value


print("ansible run_command")
print(run_command(["git", "--version"]))

print("subprocess.call")
print(run_command2(["git", "--version"]))

print("subprocess.Popen")
print(run_command3(["git", "--version"]))


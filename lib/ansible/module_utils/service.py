# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) Ansible Inc, 2016
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import glob
import os
import pickle
import platform
import select
import shlex
import subprocess
import traceback

from ansible.module_utils.six import PY2, b
from ansible.module_utils._text import to_bytes, to_text


def sysv_is_enabled(name):
    '''
    This function will check if the service name supplied
    is enabled in any of the sysv runlevels

    :arg name: name of the service to test for
    '''
    return bool(glob.glob('/etc/rc?.d/S??%s' % name))


def get_sysv_script(name):
    '''
    This function will return the expected path for an init script
    corresponding to the service name supplied.

    :arg name: name or path of the service to test for
    '''
    if name.startswith('/'):
        result = name
    else:
        result = '/etc/init.d/%s' % name

    return result


def sysv_exists(name):
    '''
    This function will return True or False depending on
    the existence of an init script corresponding to the service name supplied.

    :arg name: name of the service to test for
    '''
    return os.path.exists(get_sysv_script(name))


def fail_if_missing(module, found, service, msg=''):
    '''
    This function will return an error or exit gracefully depending on check mode status
    and if the service is missing or not.

    :arg module: is an  AnsibleModule object, used for it's utility methods
    :arg found: boolean indicating if services was found or not
    :arg service: name of service
    :kw msg: extra info to append to error/success msg when missing
    '''
    if not found:
        if module.check_mode:
            module.exit_json(msg="Service %s not found on %s, assuming it will exist on full run" % (service, msg), changed=True)
        else:
            module.fail_json(msg='Could not find the requested service %s: %s' % (service, msg))


def daemonize(module, cmd):
    '''
    Execute a command while detaching as a daemon, returns rc, stdout, and stderr.

    :arg module: is an  AnsibleModule object, used for it's utility methods
    :arg cmd: is a list or string representing the command and options to run

    This is complex because daemonization is hard for people.
    What we do is daemonize a part of this module, the daemon runs the command,
    picks up the return code and output, and returns it to the main process.
    '''

    # init some vars
    chunk = 4096  # FIXME: pass in as arg?
    errors = 'surrogate_or_strict'

    # start it!
    try:
        pipe = os.pipe()
        pid = os.fork()
    except OSError:
        module.fail_json(msg="Error while attempting to fork: %s", exception=traceback.format_exc())

    # we don't do any locking as this should be a unique module/process
    if pid == 0:

        os.close(pipe[0])
        # Set stdin/stdout/stderr to /dev/null
        fd = os.open(os.devnull, os.O_RDWR)

        # clone stdin/out/err
        for num in range(3):
            if fd != num:
                os.dup2(fd, num)

        # close otherwise
        if fd not in range(3):
            os.close(fd)

        # Make us a daemon
        pid = os.fork()

        # end if not in child
        if pid > 0:
            os._exit(0)

        # get new process session and detach
        sid = os.setsid()
        if sid == -1:
            module.fail_json(msg="Unable to detach session while daemonizing")

        # avoid possible problems with cwd being removed
        os.chdir("/")

        pid = os.fork()
        if pid > 0:
            os._exit(0)

        # if command is string deal with  py2 vs py3 conversions for shlex
        if not isinstance(cmd, list):
            if PY2:
                cmd = shlex.split(to_bytes(cmd, errors=errors))
            else:
                cmd = shlex.split(to_text(cmd, errors=errors))

        # make sure we always use byte strings
        run_cmd = []
        for c in cmd:
            run_cmd.append(to_bytes(c, errors=errors))

        # execute the command in forked process
        p = subprocess.Popen(run_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=lambda: os.close(pipe[1]))
        fds = [p.stdout, p.stderr]

        # loop reading output till its done
        output = {p.stdout: b(""), p.sterr: b("")}
        while fds:
            rfd, wfd, efd = select.select(fds, [], fds, 1)
            if (rfd + wfd + efd) or p.poll():
                for out in fds:
                    if out in rfd:
                        data = os.read(out.fileno(), chunk)
                        if not data:
                            fds.remove(out)
                    output[out] += b(data)

        # even after fds close, we might want to wait for pid to die
        p.wait()

        # Return a pickled data of parent
        return_data = pickle.dumps([p.returncode, to_text(output[p.stdout]), to_text(output[p.stderr])], protocol=pickle.HIGHEST_PROTOCOL)
        os.write(pipe[1], to_bytes(return_data, errors=errors))

        # clean up
        os.close(pipe[1])
        os._exit(0)

    elif pid == -1:
        module.fail_json(msg="Unable to fork, no exception thrown, probably due to lack of resources, check logs.")

    else:
        # in parent
        os.close(pipe[1])
        os.waitpid(pid, 0)

        # Grab response data after child finishes
        return_data = b("")
        while True:
            rfd, wfd, efd = select.select([pipe[0]], [], [pipe[0]])
            if pipe[0] in rfd:
                data = os.read(pipe[0], chunk)
                if not data:
                    break
                return_data += b(data)

        # Note: no need to specify encoding on py3 as this module sends the
        # pickle to itself (thus same python interpreter so we aren't mixing
        # py2 and py3)
        return pickle.loads(to_bytes(return_data, errors=errors))


def check_ps(module, pattern):

    # Set ps flags
    if platform.system() == 'SunOS':
        psflags = '-ef'
    else:
        psflags = 'auxww'

    # Find ps binary
    psbin = module.get_bin_path('ps', True)

    (rc, out, err) = module.run_command('%s %s' % (psbin, psflags))
    # If rc is 0, set running as appropriate
    if rc == 0:
        for line in out.split('\n'):
            if pattern in line:
                return True
    return False

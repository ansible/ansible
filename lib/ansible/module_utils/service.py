# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) Ansible Inc, 2015
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
#

import platform
import os
import shlex
import select
import subprocess
import json

class Service(object):
    """
    This is the generic Service manipulation class that is subclassed based on system.
    A subclass should override the following methods:
      - action
      - enable
      - status
    """

    def __init__(self, module):

        # states
        self.running        = None
        self.enabled        = None
        self.action         = None

        # outcome
        self.changed        = False

        # options
        self.module         = module

        # alias running to started
        if self.module.params['state'] == 'running':
            self.module.params['state'] = 'started'


    # ===========================================
    # Platform specific methods (must be replaced by subclass).

    def action(self):
        self.module.fail_json(msg="action not implemented on target service")

    def status(self): # this should also set self.enabled
        self.module.fail_json(msg="status not implemented on target service")

    def enable(self):
        self.module.fail_json(msg="enable not implemented on target service")

    # ===========================================
    # Generic methods that should be used on all services.

    def execute_command(self, cmd, daemonize=False):

        # Most things don't need to be daemonized
        if not daemonize:
            return self.module.run_command(cmd)

        # This is complex because daemonization is hard for people.
        # What we do is daemonize a part of this module, the daemon runs the
        # command, picks up the return code and output, and returns it to the
        # main process.
        pipe = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(pipe[0])
            # Set stdin/stdout/stderr to /dev/null
            fd = os.open(os.devnull, os.O_RDWR)
            if fd != 0:
                os.dup2(fd, 0)
            if fd != 1:
                os.dup2(fd, 1)
            if fd != 2:
                os.dup2(fd, 2)
            if fd not in (0, 1, 2):
                os.close(fd)

            # Make us a daemon. Yes, that's all it takes.
            pid = os.fork()
            if pid > 0:
                os._exit(0)
            os.setsid()
            os.chdir("/")
            pid = os.fork()
            if pid > 0:
                os._exit(0)

            # Start the command
            if isinstance(cmd, basestring):
                cmd = shlex.split(cmd)
            p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=lambda: os.close(pipe[1]))
            stdout = ""
            stderr = ""
            fds = [p.stdout, p.stderr]
            # Wait for all output, or until the main process is dead and its output is done.
            while fds:
                rfd, wfd, efd = select.select(fds, [], fds, 1)
                if not (rfd + wfd + efd) and p.poll() is not None:
                    break
                if p.stdout in rfd:
                    dat = os.read(p.stdout.fileno(), 4096)
                    if not dat:
                        fds.remove(p.stdout)
                    stdout += dat
                if p.stderr in rfd:
                    dat = os.read(p.stderr.fileno(), 4096)
                    if not dat:
                        fds.remove(p.stderr)
                    stderr += dat
            p.wait()
            # Return a JSON blob to parent
            os.write(pipe[1], json.dumps([p.returncode, stdout, stderr]))
            os.close(pipe[1])
            os._exit(0)
        elif pid == -1:
            self.module.fail_json(msg="unable to fork")
        else:
            os.close(pipe[1])
            os.waitpid(pid, 0)
            # Wait for data from daemon process and process it.
            data = ""
            while True:
                rfd, wfd, efd = select.select([pipe[0]], [], [pipe[0]])
                if pipe[0] in rfd:
                    dat = os.read(pipe[0], 4096)
                    if not dat:
                        break
                    data += dat
            return json.loads(data)

    def check_ps(self):

        running = False

        # Set ps flags
        if platform.system() == 'SunOS':
            psflags = '-ef'
        else:
            psflags = 'auxww'

        # Find ps binary
        psbin = self.module.get_bin_path('ps', True)

        (rc, psout, pserr) = self.execute_command('%s %s' % (psbin, psflags))
        # If rc is 0, set running as appropriate
        if rc == 0:
            lines = psout.split("\n")
            for line in lines:
                if self.module.params['pattern'] in line and not "pattern=" in line:
                    # so as to not confuse ./hacking/test-module
                    running = True
                    break

        self.running = running

    def result(self, msg=''):
        return {
                'name': self.module.name,
                'state': self.status(),
                'enabled': self.enabled,
                'changed': self.changed,
                'msg': msg,
               }

    def run(self):

        if self.module.params['state'] is None and self.module.params['enabled'] is None:
            self.module.fail_json(msg="Neither 'state' nor 'enabled' set")

        # Set service startup state on request
        if self.module.params['enabled'] is not None and self.enabled != self.module.params['enabled']:
            self.changed = True
            if not self.module.check_mode:
                self.enable()

        if self.module.params['state'] is not None and self.module.params['state'] != self.status():
            self.changed = True
            if not self.module.check_mode:
                self.action()

        return self.result()


def service_shared_arg_spec():

    return dict(
            name = dict(required=True),
            state = dict(choices=['running', 'started', 'stopped', 'restarted', 'reloaded']),
            enabled = dict(type='bool'),
    )
            # these are only needed/useful in init/rc systems
            #arguments = dict(aliases=['args'], default=''),
            #pattern = dict(required=False, default=None),
            #sleep = dict(required=False, type='int', default=None),
            #runlevel = dict(required=False, default='default'),

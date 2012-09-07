# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import warnings
import os
import pipes
import socket
import random
from ansible.callbacks import vvv
from ansible import errors

# prevent paramiko warning noise -- see http://stackoverflow.com/questions/3920502/
HAVE_PARAMIKO=False
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        import paramiko
        HAVE_PARAMIKO=True
    except ImportError:
        pass

class Connection(object):
    ''' SSH based connections with Paramiko '''

    def __init__(self, runner, host, port=None):

        self.ssh = None
        self.runner = runner
        self.host = host
        self.port = port
        if port is None:
            self.port = self.runner.remote_port

    def connect(self):
        ''' activates the connection object '''

        if not HAVE_PARAMIKO:
            raise errors.AnsibleError("paramiko is not installed")

        user = self.runner.remote_user

        vvv("ESTABLISH CONNECTION FOR USER: %s" % user, host=self.host)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        homedir = os.path.expanduser('~')
        config = paramiko.SSHConfig()
        config.parse(open(os.path.join(homedir,".ssh/config")))
        scl = config.lookup(self.host)

        try:
            if(scl):
                keyfile = (scl['identityfile']).replace('~',homedir)
                ssh.connect(scl['hostname'], username=scl['user'], allow_agent=True, look_for_keys=True,
                    key_filename=keyfile, password=self.runner.remote_pass,
                    timeout=self.runner.timeout, port=scl['port'])
            else:
                ssh.connect(self.host, username=user, allow_agent=True, look_for_keys=True,
                    key_filename=self.runner.private_key_file, password=self.runner.remote_pass,
                    timeout=self.runner.timeout, port=self.port)
        except Exception, e:
            msg = str(e)
            if "PID check failed" in msg:
                raise errors.AnsibleError("paramiko version issue, please upgrade paramiko on the machine running ansible")
            elif "Private key file is encrypted" in msg:
                msg = 'ssh %s@%s:%s : %s\nTo connect as a different user, use -u <username>.' % (
                    user, self.host, self.port, msg)
                raise errors.AnsibleConnectionFailed(msg)
            else:
                raise errors.AnsibleConnectionFailed(msg)

        self.ssh = ssh
        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False):
        ''' run a command on the remote host '''

        bufsize = 4096
        try:
            chan = self.ssh.get_transport().open_session()
        except Exception, e:
            msg = "Failed to open session"
            if len(str(e)) > 0:
                msg += ": %s" % str(e)
            raise errors.AnsibleConnectionFailed(msg)
        chan.get_pty()

        if not self.runner.sudo or not sudoable:
            quoted_command = '"$SHELL" -c ' + pipes.quote(cmd)
            vvv("EXEC %s" % quoted_command, host=self.host)
            chan.exec_command(quoted_command)
        else:
            # Rather than detect if sudo wants a password this time, -k makes
            # sudo always ask for a password if one is required. 
            # Passing a quoted compound command to sudo (or sudo -s)
            # directly doesn't work, so we shellquote it with pipes.quote()
            # and pass the quoted string to the user's shell.  We loop reading
            # output until we see the randomly-generated sudo prompt set with
            # the -p option.
            randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
            prompt = '[sudo via ansible, key=%s] password: ' % randbits
            sudocmd = 'sudo -k && sudo -p "%s" -u %s "$SHELL" -c %s' % (
                prompt, sudo_user, pipes.quote(cmd))
            vvv("EXEC %s" % sudocmd, host=self.host)
            sudo_output = ''
            try:
                chan.exec_command(sudocmd)
                if self.runner.sudo_pass:
                    while not sudo_output.endswith(prompt):
                        chunk = chan.recv(bufsize)
                        if not chunk:
                            if 'unknown user' in sudo_output:
                                raise errors.AnsibleError(
                                    'user %s does not exist' % sudo_user)
                            else:
                                raise errors.AnsibleError('ssh connection ' +
                                    'closed waiting for password prompt')
                        sudo_output += chunk
                    chan.sendall(self.runner.sudo_pass + '\n')
            except socket.timeout:
                raise errors.AnsibleError('ssh timed out waiting for sudo.\n' + sudo_output)

        return (chan.makefile('wb', bufsize), chan.makefile('rb', bufsize), '')

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        try:
            sftp = self.ssh.open_sftp()
        except:
            raise errors.AnsibleError("failed to open a SFTP connection")
        try:
            sftp.put(in_path, out_path)
        except IOError:
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)
        sftp.close()

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        try:
            sftp = self.ssh.open_sftp()
        except:
            raise errors.AnsibleError("failed to open a SFTP connection")
        try:
            sftp.get(in_path, out_path)
        except IOError:
            raise errors.AnsibleError("failed to transfer file from %s" % in_path)
        sftp.close()

    def close(self):
        ''' terminate the connection '''
        self.ssh.close()


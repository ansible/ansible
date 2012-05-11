import socket
import random
import pipes
import libssh2

from ansible import errors

class LibSSH2Connection(object):
    ''' SSH based connections with libssh2 '''

    def __init__(self, runner, host, port=None):
        session = None
        self.runner = runner
        self.host = host
        self.port = port
        if port is None:
            self.port = self.runner.remote_port

    def _get_conn(self):
        user = self.runner.remote_user

        try:
            session = libssh2.Session()
            session.set_banner()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            session.startup(sock)
            if self.runner.remote_pass:
                session.userauth_password(user, self.runner.remote_pass)
            else:
                session.userauth_agent(user)
        except Exception, e:
            raise errors.AnsibleConnectionFailed(str(e))
        return session

    def connect(self):
        ''' connect to the remote host '''

        self.session = self._get_conn()
        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False):
        ''' run a command on the remote host '''
        bufsize = 4096
        chan = self.session.open_session()

        if not self.runner.sudo or not sudoable:
            quoted_command = '"$SHELL" -c ' + pipes.quote(cmd) 
            rc = chan.execute(quoted_command)
        else:
            # Rather than detect if sudo wants a password this time, -k makes 
            # sudo always ask for a password if one is required. The "--"
            # tells sudo that this is the end of sudo options and the command
            # follows.  Passing a quoted compound command to sudo (or sudo -s)
            # directly doesn't work, so we shellquote it with pipes.quote() 
            # and pass the quoted string to the user's shell.  We loop reading
            # output until we see the randomly-generated sudo prompt set with
            # the -p option.
            randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
            prompt = '[sudo via ansible, key=%s] password: ' % randbits
            sudocmd = 'sudo -k -p "%s" -u %s -- "$SHELL" -c %s\n' % (prompt,
                    sudo_user, pipes.quote(cmd))
            sudo_output = ''
            try:
                chan.pty()
                chan.execute(sudocmd)
                if self.runner.sudo_pass:
                    while not sudo_output.endswith(prompt):
                        chunk = chan.read(bufsize)
                        if not chunk:
                            raise errors.AnsibleError('ssh connection closed waiting for sudo password prompt')
                        sudo_output += chunk
                    chan.write(self.runner.sudo_pass + '\n\n')
            except socket.timeout:
                raise errors.AnsibleError('ssh timed out waiting for sudo.\n' + sudo_output)


        data = ""
        while True:
            d = chan.read(bufsize)
            if d == "" or d is None: break
            data+=d

        stdout = data
        return "", stdout, ""

    def put_file(self, in_path, out_path, mode='644'):
        ''' transfer a file from local to remote '''
        mode = int('0' + mode, 8)
        datas=""
        f = file(in_path, "rb")
        while True:
            data = f.readline()
            if  len(data) == 0: 
                break
            else:
                datas += data
        file_size = len(datas)
        channel = self.session.scp_send(out_path, mode, file_size)
        channel.write(datas)

    def fetch_file(self, in_path, out_path):
        f = file(out_path, "wb")
        channel = self.session.scp_recv(in_path)
        bufsize = 4096
        while True:
            d = channel.read(bufsize)
            if d == "" or d is None: break
            f.write(d)
        f.close()
        channel.close()

    def close(self):
        ''' terminate the connection '''

        self.session.close()

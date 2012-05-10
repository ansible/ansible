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

    def exec_command(self, cmd, tmp_path,sudo_user,sudoable=False):

        ''' run a command on the remote host '''
        bufsize = 4096
        chan = self.session.open_session()
        
#        self.session.get_transport().open_session()
        #chan.get_pty() 

        if not self.runner.sudo or not sudoable:
            quoted_command = '"$SHELL" -c ' + pipes.quote(cmd) 
            rc = chan.execute(quoted_command)
        else:
            raise errors.AnsibleError("sudo not yet implemented for libssh2 transport")
        data = ""
        while True:
            d = chan.read(bufsize)
            if d == "" or d is None: break
            data+=d

        stdin = "" #StringIO.StringIO()
        stdout = "" #StringIO.StringIO()
        stderr = "" #StringIO.StringIO()

        stdout = data
        return stdin, stdout, stderr

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
        f = file(out_path, "w")
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

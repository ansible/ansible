""" (c) 2015, Logentries.com, Jimmy Tang <jimmy.tang@logentries.com>

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

This callback plugin will generate json objects to be sent to logentries
for auditing/debugging purposes.

Todo:

* Better formatting of output before sending out to logentries data/api nodes.

To use:

Add this to your ansible.cfg file in the defaults block

    [defaults]
    callback_plugins = ./callback_plugins
    callback_stdout = logentries
    callback_whitelist = logentries

Copy the callback plugin into the callback_plugins directory

Either set the environment variables

    export LOGENTRIES_API=data.logentries.com
    export LOGENTRIES_PORT=10000
    export LOGENTRIES_ANSIBLE_TOKEN=dd21fc88-f00a-43ff-b977-e3a4233c53af

Or create a logentries.ini config file that sites next to the plugin with the following contents

    [logentries]
    api = data.logentries.com
    port = 10000
    tls_port = 20000
    use_tls = no
    token = dd21fc88-f00a-43ff-b977-e3a4233c53af
    flatten = False


"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import socket
import random
import time
import codecs
import ConfigParser
import uuid
try:
    import certifi
    HAS_CERTIFI = True
except ImportError:
    HAS_CERTIFI = False

try:
    import flatdict
    HAS_FLATDICT = True
except ImportError:
    HAS_FLATDICT = False

from ansible.plugins.callback import CallbackBase


def to_unicode(ch):
    return codecs.unicode_escape_decode(ch)[0]


def is_unicode(ch):
    return isinstance(ch, unicode)


def create_unicode(ch):
    return unicode(ch, 'utf-8')


class PlainTextSocketAppender(object):
    def __init__(self,
                 verbose=True,
                 LE_API='data.logentries.com',
                 LE_PORT=80,
                 LE_TLS_PORT=443):

        self.LE_API = LE_API
        self.LE_PORT = LE_PORT
        self.LE_TLS_PORT = LE_TLS_PORT
        self.MIN_DELAY = 0.1
        self.MAX_DELAY = 10
        # Error message displayed when an incorrect Token has been detected
        self.INVALID_TOKEN = ("\n\nIt appears the LOGENTRIES_TOKEN "
                              "parameter you entered is incorrect!\n\n")
        # Unicode Line separator character   \u2028
        self.LINE_SEP = to_unicode('\u2028')

        self.verbose = verbose
        self._conn = None

    def open_connection(self):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((self.LE_API, self.LE_PORT))

    def reopen_connection(self):
        self.close_connection()

        root_delay = self.MIN_DELAY
        while True:
            try:
                self.open_connection()
                return
            except Exception:
                if self.verbose:
                    self._display.warning("Unable to connect to Logentries")

            root_delay *= 2
            if (root_delay > self.MAX_DELAY):
                root_delay = self.MAX_DELAY

            wait_for = root_delay + random.uniform(0, root_delay)

            try:
                time.sleep(wait_for)
            except KeyboardInterrupt:
                raise

    def close_connection(self):
        if self._conn is not None:
            self._conn.close()

    def put(self, data):
        # Replace newlines with Unicode line separator
        # for multi-line events
        if not is_unicode(data):
            multiline = create_unicode(data).replace('\n', self.LINE_SEP)
        else:
            multiline = data.replace('\n', self.LINE_SEP)
        multiline += "\n"
        # Send data, reconnect if needed
        while True:
            try:
                self._conn.send(multiline.encode('utf-8'))
            except socket.error:
                self.reopen_connection()
                continue
            break

        self.close_connection()


try:
    import ssl
    HAS_SSL=True
except ImportError:  # for systems without TLS support.
    SocketAppender = PlainTextSocketAppender
    HAS_SSL=False
else:

    class TLSSocketAppender(PlainTextSocketAppender):
        def open_connection(self):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = ssl.wrap_socket(
                sock=sock,
                keyfile=None,
                certfile=None,
                server_side=False,
                cert_reqs=ssl.CERT_REQUIRED,
                ssl_version=getattr(
                    ssl, 'PROTOCOL_TLSv1_2', ssl.PROTOCOL_TLSv1),
                ca_certs=certifi.where(),
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True, )
            sock.connect((self.LE_API, self.LE_TLS_PORT))
            self._conn = sock

    SocketAppender = TLSSocketAppender


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'logentries'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        if not HAS_SSL:
            self._display.warning("Unable to import ssl module. Will send over port 80.")

        if not HAS_CERTIFI:
            self.disabled =True
            self._display.warning('The `certifi` python module is not installed. '
                                 'Disabling the Logentries callback plugin.')

        if not HAS_FLATDICT:
            self.disabled =True
            self._display.warning('The `flatdict` python module is not installed. '
                                 'Disabling the Logentries callback plugin.')

        config_path = os.path.abspath(os.path.dirname(__file__))
        config = ConfigParser.ConfigParser()
        try:
            config.readfp(open(os.path.join(config_path, 'logentries.ini')))
            if config.has_option('logentries', 'api'):
                self.api_uri = config.get('logentries', 'api')
            if config.has_option('logentries', 'port'):
                self.api_port = config.getint('logentries', 'port')
            if config.has_option('logentries', 'tls_port'):
                self.api_tls_port = config.getint('logentries', 'tls_port')
            if config.has_option('logentries', 'use_tls'):
                self.use_tls = config.getboolean('logentries', 'use_tls')
            if config.has_option('logentries', 'token'):
                self.token = config.get('logentries', 'token')
            if config.has_option('logentries', 'flatten'):
                self.flatten = config.getboolean('logentries', 'flatten')

        except:
            self.api_uri = os.getenv('LOGENTRIES_API')
            if self.api_uri is None:
                self.api_uri = 'data.logentries.com'

            try:
                self.api_port = int(os.getenv('LOGENTRIES_PORT'))
                if self.api_port is None:
                    self.api_port = 80
            except TypeError:
                self.api_port = 80

            try:
                self.api_tls_port = int(os.getenv('LOGENTRIES_TLS_PORT'))
                if self.api_tls_port is None:
                    self.api_tls_port = 443
            except TypeError:
                self.api_tls_port = 443

            # this just needs to be set to use TLS
            self.use_tls = os.getenv('LOGENTRIES_USE_TLS')
            if self.use_tls is None:
                self.use_tls = False
            elif self.use_tls.lower() in ['yes', 'true']:
                self.use_tls = True

            self.token = os.getenv('LOGENTRIES_ANSIBLE_TOKEN')
            if self.token is None:
                self.disabled = True
                self._display.warning('Logentries token could not be loaded. The logentries token can be provided using the `LOGENTRIES_TOKEN` environment variable')

            self.flatten = os.getenv('LOGENTRIES_FLATTEN')
            if self.flatten is None:
                self.flatten = False
            elif self.flatten.lower() in ['yes', 'true']:
                self.flatten = True

        self.verbose = False
        self.timeout = 10
        self.le_jobid = str(uuid.uuid4())

        if self.use_tls:
            self._appender = TLSSocketAppender(verbose=self.verbose,
                                               LE_API=self.api_uri,
                                               LE_TLS_PORT=self.api_tls_port)
        else:
            self._appender = PlainTextSocketAppender(verbose=self.verbose,
                                                     LE_API=self.api_uri,
                                                     LE_PORT=self.api_port)
        self._appender.reopen_connection()

    def emit_formatted(self, record):
        if self.flatten:
            results = flatdict.FlatDict(record)
            self.emit(self._dump_results(results))
        else:
            self.emit(self._dump_results(record))

    def emit(self, record):
        msg = record.rstrip('\n')
        msg = "{} {}".format(self.token, msg)
        self._appender.put(msg)

    def runner_on_ok(self, host, res):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['hostname'] = host
        results['results'] = res
        results['status'] = 'OK'
        self.emit_formatted(results)

    def runner_on_failed(self, host, res, ignore_errors=False):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['hostname'] = host
        results['results'] = res
        results['status'] = 'FAILED'
        self.emit_formatted(results)

    def runner_on_skipped(self, host, item=None):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['hostname'] = host
        results['status'] = 'SKIPPED'
        self.emit_formatted(results)

    def runner_on_unreachable(self, host, res):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['hostname'] = host
        results['results'] = res
        results['status'] = 'UNREACHABLE'
        self.emit_formatted(results)

    def runner_on_async_failed(self, host, res, jid):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['hostname'] = host
        results['results'] = res
        results['jid'] = jid
        results['status'] = 'ASYNC_FAILED'
        self.emit_formatted(results)

    def v2_playbook_on_play_start(self, play):
        results = {}
        results['le_jobid'] = self.le_jobid
        results['started_by'] = os.getlogin()
        if play.name:
            results['play'] = play.name
        results['hosts'] = play.hosts
        self.emit_formatted(results)

    def playbook_on_stats(self, stats):
        """ close connection """
        self._appender.close_connection()

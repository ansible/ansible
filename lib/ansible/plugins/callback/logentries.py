# (c) 2015, Logentries.com, Jimmy Tang <jimmy.tang@logentries.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

'''
DOCUMENTATION:
    callback: logentries
    type: notification
    short_description: Sends events to Logentries
    description:
      - This callback plugin will generate JSON objects and send them to Logentries for auditing/debugging purposes.
      - If you want to use an ini configuration, the file must be placed in the same directory as this plugin and named logentries.ini
    version_added: "2.0"
    requirements:
      - whitelisting in configuration
      - certifi (python library)
      - flatdict (pytnon library)
    options:
      api:
        description: URI to the Logentries API
        env:
          - name: LOGENTRIES_API
        default: data.logentries.com
        ini:
          - section: defaults
            key: api
      port:
        description: Http port to use when connecting to the API
        env:
            - name: LOGENTRIES_PORT
        default: 80
        ini:
          - section: defaults
            key: port
      tls_port:
        description: Port to use when connecting to the API when TLS is enabled
        env:
            - name: LOGENTRIES_TLS_PORT
        default: 443
        ini:
          - section: defaults
            key: tls_port
      token:
        description: the authentication token
        env:
          - name: LOGENTRIES_ANSIBLE_TOKEN
        required: True
        ini:
          - section: defaults
            key: token
      use_tls:
        description:
          - Toggle to decidewhether to use TLS to encrypt the communications with the API server
        env:
          - name: LOGENTRIES_USE_TLS
        default: False
        type: boolean
        ini:
          - section: defaults
            key: use_tls
      flatten:
        description: flatten complex data structures into a single dictionary with complex keys
        type: boolean
        default: False
        env:
          - name: LOGENTRIES_FLATTEN
        ini:
          - section: defaults
            key: flatten
EXAMPLES: >
  To enable, add this to your ansible.cfg file in the defaults block

    [defaults]
    callback_whitelist = logentries

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
'''
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import socket
import random
import time
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

from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback import CallbackBase
"""
Todo:
  * Better formatting of output before sending out to logentries data/api nodes.
"""


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
        self.INVALID_TOKEN = ("\n\nIt appears the LOGENTRIES_TOKEN parameter you entered is incorrect!\n\n")
        # Unicode Line separator character   \u2028
        self.LINE_SEP = u'\u2028'

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
        data = to_text(data, errors='surrogate_or_strict')
        multiline = data.replace(u'\n', self.LINE_SEP)
        multiline += u"\n"
        # Send data, reconnect if needed
        while True:
            try:
                self._conn.send(to_bytes(multiline, errors='surrogate_or_strict'))
            except socket.error:
                self.reopen_connection()
                continue
            break

        self.close_connection()


try:
    import ssl
    HAS_SSL = True
except ImportError:  # for systems without TLS support.
    SocketAppender = PlainTextSocketAppender
    HAS_SSL = False
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

        warn = ''
        if not HAS_CERTIFI:
            self.disabled = True
            warn += 'The `certifi` python module is not installed.'

        if not HAS_FLATDICT:
            self.disabled = True
            warn += 'The `flatdict` python module is not installed.'

        if warn:
            self._display.warning('%s\nDisabling the Logentries callback plugin.' % warn)

        config_path = os.path.abspath(os.path.dirname(__file__))
        config = configparser.ConfigParser()
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
                self._display.warning('Logentries token could not be loaded. The logentries token can be provided using the `LOGENTRIES_TOKEN` environment '
                                      'variable')

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

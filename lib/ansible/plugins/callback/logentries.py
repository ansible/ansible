# (c) 2015, Logentries.com, Jimmy Tang <jimmy.tang@logentries.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: logentries
    type: notification
    short_description: Sends events to Logentries
    description:
      - This callback plugin will generate JSON objects and send them to Logentries via TCP for auditing/debugging purposes.
      - Before 2.4, if you wanted to use an ini configuration, the file must be placed in the same directory as this plugin and named logentries.ini
      - In 2.4 and above you can just put it in the main Ansible configuration file.
    version_added: "2.0"
    requirements:
      - whitelisting in configuration
      - certifi (python library)
      - flatdict (python library), if you want to use the 'flatten' option
    options:
      api:
        description: URI to the Logentries API
        env:
          - name: LOGENTRIES_API
        default: data.logentries.com
        ini:
          - section: callback_logentries
            key: api
      port:
        description: HTTP port to use when connecting to the API
        env:
            - name: LOGENTRIES_PORT
        default: 80
        ini:
          - section: callback_logentries
            key: port
      tls_port:
        description: Port to use when connecting to the API when TLS is enabled
        env:
            - name: LOGENTRIES_TLS_PORT
        default: 443
        ini:
          - section: callback_logentries
            key: tls_port
      token:
        description: The logentries "TCP token"
        env:
          - name: LOGENTRIES_ANSIBLE_TOKEN
        required: True
        ini:
          - section: callback_logentries
            key: token
      use_tls:
        description:
          - Toggle to decide whether to use TLS to encrypt the communications with the API server
        env:
          - name: LOGENTRIES_USE_TLS
        default: False
        type: boolean
        ini:
          - section: callback_logentries
            key: use_tls
      flatten:
        description: flatten complex data structures into a single dictionary with complex keys
        type: boolean
        default: False
        env:
          - name: LOGENTRIES_FLATTEN
        ini:
          - section: callback_logentries
            key: flatten
'''

EXAMPLES = '''
examples: >
  To enable, add this to your ansible.cfg file in the defaults block

    [defaults]
    callback_whitelist = logentries

  Either set the environment variables
    export LOGENTRIES_API=data.logentries.com
    export LOGENTRIES_PORT=10000
    export LOGENTRIES_ANSIBLE_TOKEN=dd21fc88-f00a-43ff-b977-e3a4233c53af

  Or in the main Ansible config file
    [callback_logentries]
    api = data.logentries.com
    port = 10000
    tls_port = 20000
    use_tls = no
    token = dd21fc88-f00a-43ff-b977-e3a4233c53af
    flatten = False
'''

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

from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback import CallbackBase

# Todo:
#  * Better formatting of output before sending out to logentries data/api nodes.


class PlainTextSocketAppender(object):
    def __init__(self, display, LE_API='data.logentries.com', LE_PORT=80, LE_TLS_PORT=443):

        self.LE_API = LE_API
        self.LE_PORT = LE_PORT
        self.LE_TLS_PORT = LE_TLS_PORT
        self.MIN_DELAY = 0.1
        self.MAX_DELAY = 10
        # Error message displayed when an incorrect Token has been detected
        self.INVALID_TOKEN = "\n\nIt appears the LOGENTRIES_TOKEN parameter you entered is incorrect!\n\n"
        # Unicode Line separator character   \u2028
        self.LINE_SEP = u'\u2028'

        self._display = display
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
            except Exception as e:
                self._display.vvvv(u"Unable to connect to Logentries: %s" % to_text(e))

            root_delay *= 2
            if root_delay > self.MAX_DELAY:
                root_delay = self.MAX_DELAY

            wait_for = root_delay + random.uniform(0, root_delay)

            try:
                self._display.vvvv("sleeping %s before retry" % wait_for)
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

        # TODO: allow for alternate posting methods (REST/UDP/agent/etc)
        super(CallbackModule, self).__init__()

        # verify dependencies
        if not HAS_SSL:
            self._display.warning("Unable to import ssl module. Will send over port 80.")

        if not HAS_CERTIFI:
            self.disabled = True
            self._display.warning('The `certifi` python module is not installed.\nDisabling the Logentries callback plugin.')

        self.le_jobid = str(uuid.uuid4())

        # FIXME: make configurable, move to options
        self.timeout = 10

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        # get options
        try:
            self.api_url = self.get_option('api')
            self.api_port = self.get_option('port')
            self.api_tls_port = self.get_option('tls_port')
            self.use_tls = self.get_option('use_tls')
            self.flatten = self.get_option('flatten')
        except KeyError as e:
            self._display.warning(u"Missing option for Logentries callback plugin: %s" % to_text(e))
            self.disabled = True

        try:
            self.token = self.get_option('token')
        except KeyError as e:
            self._display.warning('Logentries token was not provided, this is required for this callback to operate, disabling')
            self.disabled = True

        if self.flatten and not HAS_FLATDICT:
            self.disabled = True
            self._display.warning('You have chosen to flatten and the `flatdict` python module is not installed.\nDisabling the Logentries callback plugin.')

        self._initialize_connections()

    def _initialize_connections(self):

        if not self.disabled:
            if self.use_tls:
                self._display.vvvv("Connecting to %s:%s with TLS" % (self.api_url, self.api_tls_port))
                self._appender = TLSSocketAppender(display=self._display, LE_API=self.api_url, LE_TLS_PORT=self.api_tls_port)
            else:
                self._display.vvvv("Connecting to %s:%s" % (self.api_url, self.api_port))
                self._appender = PlainTextSocketAppender(display=self._display, LE_API=self.api_url, LE_PORT=self.api_port)
            self._appender.reopen_connection()

    def emit_formatted(self, record):
        if self.flatten:
            results = flatdict.FlatDict(record)
            self.emit(self._dump_results(results))
        else:
            self.emit(self._dump_results(record))

    def emit(self, record):
        msg = record.rstrip('\n')
        msg = "{0} {1}".format(self.token, msg)
        self._appender.put(msg)
        self._display.vvvv("Sent event to logentries")

    def _set_info(self, host, res):
        return {'le_jobid': self.le_jobid, 'hostname': host, 'results': res}

    def runner_on_ok(self, host, res):
        results = self._set_info(host, res)
        results['status'] = 'OK'
        self.emit_formatted(results)

    def runner_on_failed(self, host, res, ignore_errors=False):
        results = self._set_info(host, res)
        results['status'] = 'FAILED'
        self.emit_formatted(results)

    def runner_on_skipped(self, host, item=None):
        results = self._set_info(host, item)
        del results['results']
        results['status'] = 'SKIPPED'
        self.emit_formatted(results)

    def runner_on_unreachable(self, host, res):
        results = self._set_info(host, res)
        results['status'] = 'UNREACHABLE'
        self.emit_formatted(results)

    def runner_on_async_failed(self, host, res, jid):
        results = self._set_info(host, res)
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

# (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    author: Ansible Core Team
    name: winrm
    short_description: Run tasks over Microsoft's WinRM
    description:
        - Run commands or put/fetch on a target via WinRM
    version_added: "2.0"
    extends_documentation_fragment:
        - connection_pipelining
    requirements:
        - pywinrm >= 0.4.0 (python library)
    options:
      remote_addr:
        description:
            - Address of the windows machine
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_winrm_host
        type: str
      remote_user:
        description:
            - The user to log in as to the Windows machine
        vars:
            - name: ansible_user
            - name: ansible_winrm_user
        keyword:
            - name: remote_user
        type: str
      remote_password:
        description: Authentication password for the O(remote_user). Can be supplied as CLI option.
        vars:
            - name: ansible_password
            - name: ansible_winrm_pass
            - name: ansible_winrm_password
        type: str
        aliases:
        - password  # Needed for --ask-pass to come through on delegation
      port:
        description:
            - port for winrm to connect on remote target
            - The default is the https (5986) port, if using http it should be 5985
        vars:
          - name: ansible_port
          - name: ansible_winrm_port
        default: 5986
        keyword:
            - name: port
        type: integer
      scheme:
        description:
            - URI scheme to use
            - If not set, then will default to V(https) or V(http) if O(port) is
              V(5985).
        choices: [http, https]
        vars:
          - name: ansible_winrm_scheme
        type: str
      path:
        description: URI path to connect to
        default: '/wsman'
        vars:
          - name: ansible_winrm_path
        type: str
      transport:
        description:
           - List of winrm transports to attempt to use (ssl, plaintext, kerberos, etc)
           - If None (the default) the plugin will try to automatically guess the correct list
           - This can be set to C(basic), C(certificate), C(ntlm), C(kerberos), C(credssp).
           - It can also be set to C(plaintext) or C(ssl) but these values will use use C(basic)
             auth but over a HTTP or HTTPS connection respectively.
        type: list
        elements: str
        vars:
          - name: ansible_winrm_transport
      kerberos_command:
        description: kerberos command to use to request a authentication ticket
        default: kinit
        vars:
          - name: ansible_winrm_kinit_cmd
        type: str
      kinit_args:
        description:
        - Extra arguments to pass to C(kinit) when getting the Kerberos authentication ticket.
        - By default no extra arguments are passed into C(kinit) unless I(ansible_winrm_kerberos_delegation) is also
          set. In that case C(-f) is added to the C(kinit) args so a forwardable ticket is retrieved.
        - If set, the args will overwrite any existing defaults for C(kinit), including C(-f) for a delegated ticket.
        type: str
        vars:
          - name: ansible_winrm_kinit_args
        version_added: '2.11'
      kinit_env_vars:
        description:
        - A list of environment variables to pass through to C(kinit) when getting the Kerberos authentication ticket.
        - By default no environment variables are passed through and C(kinit) is run with a blank slate.
        - The environment variable C(KRB5CCNAME) cannot be specified here as it's used to store the temp Kerberos
          ticket used by WinRM.
        type: list
        elements: str
        default: []
        ini:
        - section: winrm
          key: kinit_env_vars
        vars:
          - name: ansible_winrm_kinit_env_vars
        version_added: '2.12'
      kerberos_mode:
        description:
            - kerberos usage mode.
            - The managed option means Ansible will obtain kerberos ticket.
            - While the manual one means a ticket must already have been obtained by the user.
            - If having issues with Ansible freezing when trying to obtain the
              Kerberos ticket, you can either set this to V(manual) and obtain
              it outside Ansible or install C(pexpect) through pip and try
              again.
        choices: [managed, manual]
        vars:
          - name: ansible_winrm_kinit_mode
        type: str
      connection_timeout:
        description:
            - Despite its name, sets both the 'operation' and 'read' timeout settings for the WinRM
              connection.
            - The operation timeout belongs to the WS-Man layer and runs on the winRM-service on the
              managed windows host.
            - The read timeout belongs to the underlying python Request call (http-layer) and runs
              on the ansible controller.
            - The operation timeout sets the WS-Man 'Operation timeout' that runs on the managed
              windows host. The operation timeout specifies how long a command will run on the
              winRM-service before it sends the message 'WinRMOperationTimeoutError' back to the
              client. The client (silently) ignores this message and starts a new instance of the
              operation timeout, waiting for the command to finish (long running commands).
            - The read timeout sets the client HTTP-request timeout and specifies how long the
              client (ansible controller) will wait for data from the server to come back over
              the HTTP-connection (timeout for waiting for in-between messages from the server).
              When this timer expires, an exception will be thrown and the ansible connection
              will be terminated with the error message 'Read timed out'
            - To avoid the above exception to be thrown, the read timeout will be set to 10
              seconds higher than the WS-Man operation timeout, thus make the connection more
              robust on networks with long latency and/or many hops between server and client
              network wise.
            - Setting the difference between the operation and the read timeout to 10 seconds
              aligns it to the defaults used in the winrm-module and the PSRP-module which also
              uses 10 seconds (30 seconds for read timeout and 20 seconds for operation timeout)
            - Corresponds to the C(operation_timeout_sec) and
              C(read_timeout_sec) args in pywinrm so avoid setting these vars
              with this one.
        vars:
          - name: ansible_winrm_connection_timeout
        type: int
      read_timeout_sec:
        description:
        - The timeout in seconds to wait for a response from the server.
        - See I(connection_timeout) for more information.
        default: 30
        type: int
        vars:
        - name: ansible_winrm_read_timeout_sec
      operation_timeout_sec:
        description:
        - The timeout in seconds to wait for a single WSMan operation.
        - See I(connection_timeout) for more information.
        default: 20
        type: int
        vars:
        - name: ansible_winrm_operation_timeout_sec
      message_encryption:
        description:
        - Sets the WinRM message encryption behaviour.
        - WinRM message encryption is the encryption of the WinRM messages when
          using the C(ntlm), C(kerberos), or C(credssp) authentication options.
        - C(always) will always use message encryption even if running over a
          HTTPS connection. This will fail if using an authentication method
          that does not support message encryption like C(basic) or
          C(certificate).
        - C(auto) will enable message encryption if running over a HTTP
          listener and the authentication method is C(ntlm), C(kerberos), or
          C(credssp). If running over a HTTPS listener, message encryption is
          not used as HTTPS already encrypts the data. If using an auth method
          that does not support message encryption, no encryption will be used
          even over a HTTP listener.
        - C(never) will never use message encryption even over a HTTP listener.
          This is only recommended for debugging purposes as any data exchanged
          will be readable by anyone on the network.
        choices:
        - always
        - auto
        - never
        default: auto
        type: str
        vars:
        - name: ansible_winrm_message_encryption
      proxy:
        description:
        - Sets the proxy host to use for the WinRM connection.
        - This can be set to the string C(None) to disable the proxy and not
          lookup any proxy settings from the environment.
        type: str
        vars:
        - name: ansible_winrm_proxy
      cert_pem:
        description:
        - The path to the local file that is a PEM encoded certificate to use
          for authentication when C(transport=certificate).
        - Use I(cert_key_pem) to specify the path to the PEM encoded private
          key file.
        type: str
        vars:
        - name: ansible_winrm_cert_pem
      cert_key_pem:
        description:
        - The path to the local file that is a PEM encoded private key to use
          for authentication when C(transport=certificate).
        - The PEM encoded private key must not be encrypted as the underlying
          WinRM library only supports plaintext keys.
        - Use I(cert_pem) to specify the path to the PEM encoded public
          certificate.
        type: str
        vars:
        - name: ansible_winrm_cert_key_pem
      ca_trust_path:
        description:
        - The path to a PEM encoded CA file or OpenSSL CA directory bundle to
          use for the root CA checks.
        - If unset, the default CA trust store set by the C(requests) Python
          library will be used.
        type: str
        vars:
        - name: ansible_winrm_ca_trust_path
      server_cert_validation:
        description:
        - The HTTPS server certificate validation behaviour.
        - C(validate) will validate the server certificate against the CA trust
          store and check that the CN/SAN matches the hostname requested.
        - C(ignore) will ignore any CA and CN validation checks.
        - Using C(ignore) is not recommended in production environments as it
          disables server identity verification checks.
        - The I(ca_trust_path) option can be used to specify the path to a
          custom CA trust store to be used for validation.
        choices:
        - ignore
        - validate
        default: validate
        type: str
        vars:
        - name: ansible_winrm_server_cert_validation
      kerberos_delegation:
        description:
        - Request that Kerberos unconstrained delegation be used with
          Kerberos authentication.
        - Unconstrained delegation is a way to overcome the double-hop problem
          with WinRM.
        - If not using a Kerberos ticket managed by Ansible, the credential
          stored by kinit must be a forwardable ticket for delegation to be
          available.
        type: bool
        default: false
        vars:
        - name: ansible_winrm_kerberos_delegation
      kerberos_hostname_override:
        description:
        - Sets the hostname portion of the SPN used when requesting the
          Kerberos ticket.
        - By default the hostname is the value of the C(remote_addr) option
          but this option can be used to set a different hostname for the SPN.
        type: str
        vars:
        - name: ansible_winrm_kerberos_hostname_override
      kerberos_service:
        description:
        - The Kerberos service name, if unset the default service name of
           C(HTTP) will be used.
        type: str
        vars:
        # _service is used for backwards compatibility with the old _extras
        # lookup.
        - name: ansible_winrm_service
        - name: ansible_winrm_kerberos_service
      send_cbt:
        description:
        - Controls whether the channel binding token authentication binding is
          used with C(ntlm) or C(kerberos) authentication.
        - This should be C(true) but can be set to C(false) for debugging
          purposes.
        type: bool
        default: true
        vars:
        - name: ansible_winrm_send_cbt
"""

import base64
import ipaddress
import logging
import os
import re
import traceback
import json
import tempfile
import shlex
import subprocess
import time
import typing as t
import xml.etree.ElementTree as ET

from inspect import getfullargspec
from urllib.parse import urlunsplit

HAVE_KERBEROS = False
try:
    import kerberos  # pylint: disable=unused-import
    HAVE_KERBEROS = True
except ImportError:
    pass

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils.json_utils import _filter_non_json_lines
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import _parse_clixml
from ansible.plugins.shell.powershell import ShellBase as PowerShellBase
from ansible.utils.hashing import secure_hash
from ansible.utils.display import Display


try:
    import winrm
    from winrm.exceptions import WinRMError, WinRMOperationTimeoutError, WinRMTransportError
    from winrm.protocol import Protocol
    import requests.exceptions
    HAS_WINRM = True
    WINRM_IMPORT_ERR = None
except ImportError as e:
    HAS_WINRM = False
    WINRM_IMPORT_ERR = e

try:
    from winrm.exceptions import WSManFaultError
except ImportError:
    # This was added in pywinrm 0.5.0, we just use our no-op exception for
    # older versions which won't be able to handle this scenario.
    class WSManFaultError(Exception):  # type: ignore[no-redef]
        pass

try:
    import xmltodict
    HAS_XMLTODICT = True
    XMLTODICT_IMPORT_ERR = None
except ImportError as e:
    HAS_XMLTODICT = False
    XMLTODICT_IMPORT_ERR = e

HAS_PEXPECT = False
try:
    import pexpect
    # echo was added in pexpect 3.3+ which is newer than the RHEL package
    # we can only use pexpect for kerb auth if echo is a valid kwarg
    # https://github.com/ansible/ansible/issues/43462
    if hasattr(pexpect, 'spawn'):
        argspec = getfullargspec(pexpect.spawn.__init__)
        if 'echo' in argspec.args:
            HAS_PEXPECT = True
except ImportError as e:
    pass


display = Display()


class Connection(ConnectionBase):
    """WinRM connections over HTTP/HTTPS."""

    transport = 'winrm'
    module_implementation_preferences = ('.ps1', '.exe', '')
    allow_executable = False
    has_pipelining = True

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:

        self.always_pipeline_modules = True
        self.has_native_async = True

        self.protocol: winrm.Protocol | None = None
        self.shell_id: str | None = None
        self.delegate = None
        self._shell: PowerShellBase
        self._shell_type = 'powershell'

        super(Connection, self).__init__(*args, **kwargs)

        if not C.DEFAULT_DEBUG:
            logging.getLogger('requests_credssp').setLevel(logging.INFO)
            logging.getLogger('requests_kerberos').setLevel(logging.INFO)
            logging.getLogger('urllib3').setLevel(logging.INFO)

    def _build_winrm_kwargs(self) -> None:
        # this used to be in set_options, as win_reboot needs to be able to
        # override the conn timeout, we need to be able to build the args
        # after setting individual options. This is called by _connect before
        # starting the WinRM connection
        self._winrm_host = self.get_option('remote_addr')
        self._winrm_user = self.get_option('remote_user')
        self._winrm_pass = self.get_option('remote_password')

        self._winrm_port = self.get_option('port')

        self._winrm_scheme = self.get_option('scheme')
        # old behaviour, scheme should default to http if not set and the port
        # is 5985 otherwise https
        if self._winrm_scheme is None:
            self._winrm_scheme = 'http' if self._winrm_port == 5985 else 'https'

        self._winrm_path = self.get_option('path')
        self._kinit_cmd = self.get_option('kerberos_command')
        self._winrm_transport = self.get_option('transport')
        self._winrm_connection_timeout = self.get_option('connection_timeout')

        # calculate transport if needed
        if self._winrm_transport is None or self._winrm_transport[0] is None:
            # TODO: figure out what we want to do with auto-transport selection in the face of NTLM/Kerb/CredSSP/Cert/Basic
            transport_selector = ['ssl'] if self._winrm_scheme == 'https' else ['plaintext']

            if HAVE_KERBEROS and ((self._winrm_user and '@' in self._winrm_user)):
                self._winrm_transport = ['kerberos'] + transport_selector
            else:
                self._winrm_transport = transport_selector

        # if kerberos is among our transports and there's a password specified, we're managing the tickets
        kinit_mode = self.get_option('kerberos_mode')
        if kinit_mode is None:
            # HACK: ideally, remove multi-transport stuff
            self._kerb_managed = "kerberos" in self._winrm_transport and (self._winrm_pass is not None and self._winrm_pass != "")
        elif kinit_mode == "managed":
            self._kerb_managed = True
        elif kinit_mode == "manual":
            self._kerb_managed = False

        self._winrm_kwargs = dict(
            username=self._winrm_user,
            password=self._winrm_pass,
            service=self.get_option('kerberos_service'),
            cert_pem=self.get_option('cert_pem'),
            cert_key_pem=self.get_option('cert_key_pem'),
            server_cert_validation=self.get_option('server_cert_validation'),
            kerberos_delegation=self.get_option('kerberos_delegation'),
            read_timeout_sec=self.get_option('read_timeout_sec'),
            operation_timeout_sec=self.get_option('operation_timeout_sec'),
            kerberos_hostname_override=self.get_option('kerberos_hostname_override'),
            message_encryption=self.get_option('message_encryption'),
            send_cbt=self.get_option('send_cbt'),
        )

        # These two options are special, the default is deprecated and be
        # removed/changed in a future pywinrm version. We keep it unset in the
        # kwargs unless explicitly set.
        if ca_trust_path := self.get_option('ca_trust_path'):
            self._winrm_kwargs['ca_trust_path'] = ca_trust_path

        if proxy := self.get_option('proxy'):
            self._winrm_kwargs['proxy'] = None if proxy.lower() == 'none' else proxy

    # Until pykerberos has enough goodies to implement a rudimentary kinit/klist, simplest way is to let each connection
    # auth itself with a private CCACHE.
    def _kerb_auth(self, principal: str, password: str) -> None:
        if password is None:
            password = ""

        self._kerb_ccache = tempfile.NamedTemporaryFile()
        display.vvvvv("creating Kerberos CC at %s" % self._kerb_ccache.name)
        krb5ccname = "FILE:%s" % self._kerb_ccache.name
        os.environ["KRB5CCNAME"] = krb5ccname
        krb5env = dict(PATH=os.environ["PATH"], KRB5CCNAME=krb5ccname)

        # Add any explicit environment vars into the krb5env block
        kinit_env_vars = self.get_option('kinit_env_vars')
        for var in kinit_env_vars:
            if var not in krb5env and var in os.environ:
                krb5env[var] = os.environ[var]

        # Stores various flags to call with kinit, these could be explicit args set by 'ansible_winrm_kinit_args' OR
        # '-f' if kerberos delegation is requested (ansible_winrm_kerberos_delegation).
        kinit_cmdline = [self._kinit_cmd]
        kinit_args = self.get_option('kinit_args')
        if kinit_args:
            kinit_args = [to_text(a) for a in shlex.split(kinit_args) if a.strip()]
            kinit_cmdline.extend(kinit_args)

        elif boolean(self.get_option('kerberos_delegation')):
            kinit_cmdline.append('-f')

        kinit_cmdline.append(principal)

        # pexpect runs the process in its own pty so it can correctly send
        # the password as input even on MacOS which blocks subprocess from
        # doing so. Unfortunately it is not available on the built in Python
        # so we can only use it if someone has installed it
        if HAS_PEXPECT:
            proc_mechanism = "pexpect"
            command = kinit_cmdline.pop(0)
            password = to_text(password, encoding='utf-8',
                               errors='surrogate_or_strict')

            display.vvvv("calling kinit with pexpect for principal %s"
                         % principal)
            try:
                child = pexpect.spawn(command, kinit_cmdline, timeout=60,
                                      env=krb5env, echo=False)
            except pexpect.ExceptionPexpect as err:
                err_msg = "Kerberos auth failure when calling kinit cmd " \
                          "'%s': %s" % (command, to_native(err))
                raise AnsibleConnectionFailure(err_msg)

            try:
                child.expect(".*:")
                child.sendline(password)
            except OSError as err:
                # child exited before the pass was sent, Ansible will raise
                # error based on the rc below, just display the error here
                display.vvvv("kinit with pexpect raised OSError: %s"
                             % to_native(err))

            # technically this is the stdout + stderr but to match the
            # subprocess error checking behaviour, we will call it stderr
            stderr = child.read()
            child.wait()
            rc = child.exitstatus
        else:
            proc_mechanism = "subprocess"
            b_password = to_bytes(password, encoding='utf-8',
                                  errors='surrogate_or_strict')

            display.vvvv("calling kinit with subprocess for principal %s"
                         % principal)
            try:
                p = subprocess.Popen(kinit_cmdline, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     env=krb5env)

            except OSError as err:
                err_msg = "Kerberos auth failure when calling kinit cmd " \
                          "'%s': %s" % (self._kinit_cmd, to_native(err))
                raise AnsibleConnectionFailure(err_msg)

            stdout, stderr = p.communicate(b_password + b'\n')
            rc = p.returncode != 0

        if rc != 0:
            # one last attempt at making sure the password does not exist
            # in the output
            exp_msg = to_native(stderr.strip())
            exp_msg = exp_msg.replace(to_native(password), "<redacted>")

            err_msg = "Kerberos auth failure for principal %s with %s: %s" \
                      % (principal, proc_mechanism, exp_msg)
            raise AnsibleConnectionFailure(err_msg)

        display.vvvvv("kinit succeeded for principal %s" % principal)

    def _winrm_connect(self) -> winrm.Protocol:
        """
        Establish a WinRM connection over HTTP/HTTPS.
        """
        display.vvv("ESTABLISH WINRM CONNECTION FOR USER: %s on PORT %s TO %s" %
                    (self._winrm_user, self._winrm_port, self._winrm_host), host=self._winrm_host)

        winrm_host = self._winrm_host
        display.debug("checking if winrm_host %s is an IPv6 address" % winrm_host)
        try:
            ipaddress.IPv6Address(winrm_host)
        except ipaddress.AddressValueError:
            pass
        else:
            winrm_host = "[%s]" % winrm_host

        netloc = '%s:%d' % (winrm_host, self._winrm_port)
        endpoint = urlunsplit((self._winrm_scheme, netloc, self._winrm_path, '', ''))
        errors = []
        for transport in self._winrm_transport:
            if transport == 'kerberos':
                if not HAVE_KERBEROS:
                    errors.append('kerberos: the python kerberos library is not installed')
                    continue
                if self._kerb_managed:
                    self._kerb_auth(self._winrm_user, self._winrm_pass)
            display.vvvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint), host=self._winrm_host)
            try:
                winrm_kwargs = self._winrm_kwargs.copy()
                if self._winrm_connection_timeout:
                    winrm_kwargs['operation_timeout_sec'] = self._winrm_connection_timeout
                    winrm_kwargs['read_timeout_sec'] = self._winrm_connection_timeout + 10
                protocol = Protocol(endpoint, transport=transport, **winrm_kwargs)

                # open the shell from connect so we know we're able to talk to the server
                if not self.shell_id:
                    self.shell_id = protocol.open_shell(codepage=65001)  # UTF-8
                    display.vvvvv('WINRM OPEN SHELL: %s' % self.shell_id, host=self._winrm_host)

                return protocol
            except Exception as e:
                err_msg = to_text(e).strip()
                if re.search(to_text(r'Operation\s+?timed\s+?out'), err_msg, re.I):
                    raise AnsibleError('the connection attempt timed out')
                m = re.search(to_text(r'Code\s+?(\d{3})'), err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 401:
                        err_msg = 'the specified credentials were rejected by the server'
                    elif code == 411:
                        return protocol
                errors.append(u'%s: %s' % (transport, err_msg))
                display.vvvvv(u'WINRM CONNECTION ERROR: %s\n%s' % (err_msg, to_text(traceback.format_exc())), host=self._winrm_host)
        if errors:
            raise AnsibleConnectionFailure(', '.join(map(to_native, errors)))
        else:
            raise AnsibleError('No transport found for WinRM connection')

    def _winrm_write_stdin(self, command_id: str, stdin_iterator: t.Iterable[tuple[bytes, bool]]) -> None:
        for (data, is_last) in stdin_iterator:
            for attempt in range(1, 4):
                try:
                    self._winrm_send_input(self.protocol, self.shell_id, command_id, data, eof=is_last)

                except WinRMOperationTimeoutError:
                    # A WSMan OperationTimeout can be received for a Send
                    # operation when the server is under severe load. On manual
                    # testing the input is still processed and it's safe to
                    # continue. As the calling method still tries to wait for
                    # the proc to end if this failed it shouldn't hurt to just
                    # treat this as a warning.
                    display.warning(
                        "WSMan OperationTimeout during send input, attempting to continue. "
                        "If this continues to occur, try increasing the connection_timeout "
                        "value for this host."
                    )
                    if not is_last:
                        time.sleep(5)

                except WinRMError as e:
                    # Error 170 == ERROR_BUSY. This could be the result of a
                    # timed out Send from above still being processed on the
                    # server. Add a 5 second delay and try up to 3 times before
                    # fully giving up.
                    # pywinrm does not expose the internal WSMan fault details
                    # through an actual object but embeds it as a repr.
                    if attempt == 3 or "'wsmanfault_code': '170'" not in str(e):
                        raise

                    display.warning(f"WSMan send failed on attempt {attempt} as the command is busy, trying to send data again")
                    time.sleep(5)
                    continue

                break

    def _winrm_send_input(self, protocol: winrm.Protocol, shell_id: str, command_id: str, stdin: bytes, eof: bool = False) -> None:
        rq = {'env:Envelope': protocol._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Send',
            shell_id=shell_id)}
        stream = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Send', {})\
            .setdefault('rsp:Stream', {})
        stream['@Name'] = 'stdin'
        stream['@CommandId'] = command_id
        stream['#text'] = base64.b64encode(to_bytes(stdin))
        if eof:
            stream['@End'] = 'true'
        protocol.send_message(xmltodict.unparse(rq))

    def _winrm_get_raw_command_output(
        self,
        protocol: winrm.Protocol,
        shell_id: str,
        command_id: str,
    ) -> tuple[bytes, bytes, int, bool]:
        rq = {'env:Envelope': protocol._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive',
            shell_id=shell_id)}

        stream = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Receive', {})\
            .setdefault('rsp:DesiredStream', {})
        stream['@CommandId'] = command_id
        stream['#text'] = 'stdout stderr'

        res = protocol.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(res)
        stream_nodes = [
            node for node in root.findall('.//*')
            if node.tag.endswith('Stream')]
        stdout = []
        stderr = []
        return_code = -1
        for stream_node in stream_nodes:
            if not stream_node.text:
                continue
            if stream_node.attrib['Name'] == 'stdout':
                stdout.append(base64.b64decode(stream_node.text.encode('ascii')))
            elif stream_node.attrib['Name'] == 'stderr':
                stderr.append(base64.b64decode(stream_node.text.encode('ascii')))

        command_done = len([
            node for node in root.findall('.//*')
            if node.get('State', '').endswith('CommandState/Done')]) == 1
        if command_done:
            return_code = int(
                next(node for node in root.findall('.//*')
                     if node.tag.endswith('ExitCode')).text)

        return b"".join(stdout), b"".join(stderr), return_code, command_done

    def _winrm_get_command_output(
        self,
        protocol: winrm.Protocol,
        shell_id: str,
        command_id: str,
        try_once: bool = False,
    ) -> tuple[bytes, bytes, int]:
        stdout_buffer, stderr_buffer = [], []
        command_done = False
        return_code = -1

        while not command_done:
            try:
                stdout, stderr, return_code, command_done = \
                    self._winrm_get_raw_command_output(protocol, shell_id, command_id)
                stdout_buffer.append(stdout)
                stderr_buffer.append(stderr)

                # If we were able to get output at least once then we should be
                # able to get the rest.
                try_once = False
            except WinRMOperationTimeoutError:
                # This is an expected error when waiting for a long-running process,
                # just silently retry if we haven't been set to do one attempt.
                if try_once:
                    break
                continue
        return b''.join(stdout_buffer), b''.join(stderr_buffer), return_code

    def _winrm_exec(
        self,
        command: str,
        args: t.Iterable[bytes] = (),
        from_exec: bool = False,
        stdin_iterator: t.Iterable[tuple[bytes, bool]] = None,
    ) -> tuple[int, bytes, bytes]:
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
        if from_exec:
            display.vvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        else:
            display.vvvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        command_id = None
        try:
            stdin_push_failed = False
            command_id = self._winrm_run_command(
                to_bytes(command),
                tuple(map(to_bytes, args)),
                console_mode_stdin=(stdin_iterator is None),
            )

            try:
                if stdin_iterator:
                    self._winrm_write_stdin(command_id, stdin_iterator)

            except Exception as ex:
                display.warning("ERROR DURING WINRM SEND INPUT - attempting to recover: %s %s"
                                % (type(ex).__name__, to_text(ex)))
                display.debug(traceback.format_exc())
                stdin_push_failed = True

            # Even on a failure above we try at least once to get the output
            # in case the stdin was actually written and it an normally.
            b_stdout, b_stderr, rc = self._winrm_get_command_output(
                self.protocol,
                self.shell_id,
                command_id,
                try_once=stdin_push_failed,
            )
            stdout = to_text(b_stdout)
            stderr = to_text(b_stderr)

            if from_exec:
                display.vvvvv('WINRM RESULT <Response code %d, out %r, err %r>' % (rc, stdout, stderr), host=self._winrm_host)
            display.vvvvvv('WINRM RC %d' % rc, host=self._winrm_host)
            display.vvvvvv('WINRM STDOUT %s' % stdout, host=self._winrm_host)
            display.vvvvvv('WINRM STDERR %s' % stderr, host=self._winrm_host)

            # This is done after logging so we can still see the raw stderr for
            # debugging purposes.
            if b_stderr.startswith(b"#< CLIXML"):
                b_stderr = _parse_clixml(b_stderr)
                stderr = to_text(stderr)

            if stdin_push_failed:
                # There are cases where the stdin input failed but the WinRM service still processed it. We attempt to
                # see if stdout contains a valid json return value so we can ignore this error
                try:
                    filtered_output, dummy = _filter_non_json_lines(stdout)
                    json.loads(filtered_output)
                except ValueError:
                    # stdout does not contain a return response, stdin input was a fatal error
                    raise AnsibleError(f'winrm send_input failed; \nstdout: {stdout}\nstderr {stderr}')

            return rc, b_stdout, b_stderr
        except requests.exceptions.Timeout as exc:
            raise AnsibleConnectionFailure('winrm connection error: %s' % to_native(exc))
        finally:
            if command_id:
                # Due to a bug in how pywinrm works with message encryption we
                # ignore a 400 error which can occur when a task timeout is
                # set and the code tries to clean up the command. This happens
                # as the cleanup msg is sent over a new socket but still uses
                # the already encrypted payload bound to the other socket
                # causing the server to reply with 400 Bad Request.
                try:
                    self.protocol.cleanup_command(self.shell_id, command_id)
                except WinRMTransportError as e:
                    if e.code != 400:
                        raise

                    display.warning("Failed to cleanup running WinRM command, resources might still be in use on the target server")

    def _winrm_run_command(
        self,
        command: bytes,
        args: tuple[bytes, ...],
        console_mode_stdin: bool = False,
    ) -> str:
        """Starts a command with handling when the WSMan quota is exceeded."""
        try:
            return self.protocol.run_command(
                self.shell_id,
                command,
                args,
                console_mode_stdin=console_mode_stdin,
            )
        except WSManFaultError as fault_error:
            if fault_error.wmierror_code != 0x803381A6:
                raise

            # 0x803381A6 == ERROR_WSMAN_QUOTA_MAX_OPERATIONS
            # WinRS does not decrement the operation count for commands,
            # only way to avoid this is to re-create the shell. This is
            # important for action plugins that might be running multiple
            # processes in the same connection.
            display.vvvvv("Shell operation quota exceeded, re-creating shell", host=self._winrm_host)
            self.close()
            self._connect()
            return self.protocol.run_command(
                self.shell_id,
                command,
                args,
                console_mode_stdin=console_mode_stdin,
            )

    def _connect(self) -> Connection:

        if not HAS_WINRM:
            raise AnsibleError("winrm or requests is not installed: %s" % to_native(WINRM_IMPORT_ERR))
        elif not HAS_XMLTODICT:
            raise AnsibleError("xmltodict is not installed: %s" % to_native(XMLTODICT_IMPORT_ERR))

        super(Connection, self)._connect()
        if not self.protocol:
            self._build_winrm_kwargs()  # build the kwargs from the options set
            self.protocol = self._winrm_connect()
            self._connected = True
        return self

    def reset(self) -> None:
        if not self._connected:
            return
        self.protocol = None
        self.shell_id = None
        self._connect()

    def _wrapper_payload_stream(self, payload: bytes, buffer_size: int = 200000) -> t.Iterable[tuple[bytes, bool]]:
        payload_bytes = to_bytes(payload)
        byte_count = len(payload_bytes)
        for i in range(0, byte_count, buffer_size):
            yield payload_bytes[i:i + buffer_size], i + buffer_size >= byte_count

    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        cmd_parts = self._shell._encode_script(cmd, as_list=True, strict_mode=False, preserve_rc=False)

        # TODO: display something meaningful here
        display.vvv("EXEC (via pipeline wrapper)")

        stdin_iterator = None

        if in_data:
            stdin_iterator = self._wrapper_payload_stream(in_data)

        return self._winrm_exec(cmd_parts[0], cmd_parts[1:], from_exec=True, stdin_iterator=stdin_iterator)

    # FUTURE: determine buffer size at runtime via remote winrm config?
    def _put_file_stdin_iterator(self, in_path: str, out_path: str, buffer_size: int = 250000) -> t.Iterable[tuple[bytes, bool]]:
        in_size = os.path.getsize(to_bytes(in_path, errors='surrogate_or_strict'))
        offset = 0
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            for out_data in iter((lambda: in_file.read(buffer_size)), b''):
                offset += len(out_data)
                self._display.vvvvv('WINRM PUT "%s" to "%s" (offset=%d size=%d)' % (in_path, out_path, offset, len(out_data)), host=self._winrm_host)
                # yes, we're double-encoding over the wire in this case- we want to ensure that the data shipped to the end PS pipeline is still b64-encoded
                b64_data = base64.b64encode(out_data) + b'\r\n'
                # cough up the data, as well as an indicator if this is the last chunk so winrm_send knows to set the End signal
                yield b64_data, (in_file.tell() == in_size)

            if offset == 0:  # empty file, return an empty buffer + eof to close it
                yield b"", True

    def put_file(self, in_path: str, out_path: str) -> None:
        super(Connection, self).put_file(in_path, out_path)
        out_path = self._shell._unquote(out_path)
        display.vvv('PUT "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % to_native(in_path))

        script_template = u"""
            begin {{
                $path = '{0}'

                $DebugPreference = "Continue"
                $ErrorActionPreference = "Stop"
                Set-StrictMode -Version 2

                $fd = [System.IO.File]::Create($path)

                $sha1 = [System.Security.Cryptography.SHA1CryptoServiceProvider]::Create()

                $bytes = @() #initialize for empty file case
            }}
            process {{
               $bytes = [System.Convert]::FromBase64String($input)
               $sha1.TransformBlock($bytes, 0, $bytes.Length, $bytes, 0) | Out-Null
               $fd.Write($bytes, 0, $bytes.Length)
            }}
            end {{
                $sha1.TransformFinalBlock($bytes, 0, 0) | Out-Null

                $hash = [System.BitConverter]::ToString($sha1.Hash).Replace("-", "").ToLowerInvariant()

                $fd.Close()

                Write-Output "{{""sha1"":""$hash""}}"
            }}
        """

        script = script_template.format(self._shell._escape(out_path))
        cmd_parts = self._shell._encode_script(script, as_list=True, strict_mode=False, preserve_rc=False)

        status_code, b_stdout, b_stderr = self._winrm_exec(cmd_parts[0], cmd_parts[1:], stdin_iterator=self._put_file_stdin_iterator(in_path, out_path))
        stdout = to_text(b_stdout)
        stderr = to_text(b_stderr)

        if status_code != 0:
            raise AnsibleError(stderr)

        try:
            put_output = json.loads(stdout)
        except ValueError:
            # stdout does not contain a valid response
            raise AnsibleError('winrm put_file failed; \nstdout: %s\nstderr %s' % (stdout, stderr))

        remote_sha1 = put_output.get("sha1")
        if not remote_sha1:
            raise AnsibleError("Remote sha1 was not returned")

        local_sha1 = secure_hash(in_path)

        if not remote_sha1 == local_sha1:
            raise AnsibleError("Remote sha1 hash {0} does not match local hash {1}".format(to_native(remote_sha1), to_native(local_sha1)))

    def fetch_file(self, in_path: str, out_path: str) -> None:
        super(Connection, self).fetch_file(in_path, out_path)
        in_path = self._shell._unquote(in_path)
        out_path = out_path.replace('\\', '/')
        # consistent with other connection plugins, we assume the caller has created the target dir
        display.vvv('FETCH "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        buffer_size = 2**19  # 0.5MB chunks
        out_file = None
        try:
            offset = 0
            while True:
                try:
                    script = """
                        $path = '%(path)s'
                        If (Test-Path -LiteralPath $path -PathType Leaf)
                        {
                            $buffer_size = %(buffer_size)d
                            $offset = %(offset)d

                            $stream = New-Object -TypeName IO.FileStream($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
                            $stream.Seek($offset, [System.IO.SeekOrigin]::Begin) > $null
                            $buffer = New-Object -TypeName byte[] $buffer_size
                            $bytes_read = $stream.Read($buffer, 0, $buffer_size)
                            if ($bytes_read -gt 0) {
                                $bytes = $buffer[0..($bytes_read - 1)]
                                [System.Convert]::ToBase64String($bytes)
                            }
                            $stream.Close() > $null
                        }
                        ElseIf (Test-Path -LiteralPath $path -PathType Container)
                        {
                            Write-Host "[DIR]";
                        }
                        Else
                        {
                            Write-Error "$path does not exist";
                            Exit 1;
                        }
                    """ % dict(buffer_size=buffer_size, path=self._shell._escape(in_path), offset=offset)
                    display.vvvvv('WINRM FETCH "%s" to "%s" (offset=%d)' % (in_path, out_path, offset), host=self._winrm_host)
                    cmd_parts = self._shell._encode_script(script, as_list=True, preserve_rc=False)
                    status_code, b_stdout, b_stderr = self._winrm_exec(cmd_parts[0], cmd_parts[1:])
                    stdout = to_text(b_stdout)
                    stderr = to_text(b_stderr)

                    if status_code != 0:
                        raise IOError(stderr)
                    if stdout.strip() == '[DIR]':
                        data = None
                    else:
                        data = base64.b64decode(stdout.strip())
                    if data is None:
                        break
                    else:
                        if not out_file:
                            # If out_path is a directory and we're expecting a file, bail out now.
                            if os.path.isdir(to_bytes(out_path, errors='surrogate_or_strict')):
                                break
                            out_file = open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb')
                        out_file.write(data)
                        if len(data) < buffer_size:
                            break
                        offset += len(data)
                except Exception:
                    traceback.print_exc()
                    raise AnsibleError('failed to transfer file to "%s"' % to_native(out_path))
        finally:
            if out_file:
                out_file.close()

    def close(self) -> None:
        if self.protocol and self.shell_id:
            display.vvvvv('WINRM CLOSE SHELL: %s' % self.shell_id, host=self._winrm_host)
            self.protocol.close_shell(self.shell_id)
        self.shell_id = None
        self.protocol = None
        self._connected = False

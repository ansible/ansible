# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
author: Ansible Core Team
name: psrp
short_description: Run tasks over Microsoft PowerShell Remoting Protocol
description:
- Run commands or put/fetch on a target via PSRP (WinRM plugin)
- This is similar to the P(ansible.builtin.winrm#connection) connection plugin which uses the same
  underlying transport but instead runs in a PowerShell interpreter.
version_added: "2.7"
requirements:
- pypsrp>=0.4.0, <1.0.0 (Python library)
extends_documentation_fragment:
    - connection_pipelining
options:
  # transport options
  remote_addr:
    description:
    - The hostname or IP address of the remote host.
    default: inventory_hostname
    type: str
    vars:
    - name: inventory_hostname
    - name: ansible_host
    - name: ansible_psrp_host
  remote_user:
    description:
    - The user to log in as.
    type: str
    vars:
    - name: ansible_user
    - name: ansible_psrp_user
    keyword:
    - name: remote_user
  remote_password:
    description: Authentication password for the O(remote_user). Can be supplied as CLI option.
    type: str
    vars:
    - name: ansible_password
    - name: ansible_winrm_pass
    - name: ansible_winrm_password
    aliases:
    - password  # Needed for --ask-pass to come through on delegation
  port:
    description:
    - The port for PSRP to connect on the remote target.
    - Default is V(5986) if O(protocol) is not defined or is V(https),
      otherwise the port is V(5985).
    type: int
    vars:
    - name: ansible_port
    - name: ansible_psrp_port
    keyword:
    - name: port
  protocol:
    description:
    - Set the protocol to use for the connection.
    - Default is V(https) if O(port) is not defined or O(port) is not V(5985).
    choices:
    - http
    - https
    type: str
    vars:
    - name: ansible_psrp_protocol
  path:
    description:
    - The URI path to connect to.
    type: str
    vars:
    - name: ansible_psrp_path
    default: 'wsman'
  auth:
    description:
    - The authentication protocol to use when authenticating the remote user.
    - The default, V(negotiate), will attempt to use Kerberos (V(kerberos)) if it is
      available and fall back to NTLM (V(ntlm)) if it isn't.
    type: str
    vars:
    - name: ansible_psrp_auth
    choices:
    - basic
    - certificate
    - negotiate
    - kerberos
    - ntlm
    - credssp
    default: negotiate
  cert_validation:
    description:
    - Whether to validate the remote server's certificate or not.
    - Set to V(ignore) to not validate any certificates.
    - O(ca_cert) can be set to the path of a PEM certificate chain to
      use in the validation.
    choices:
    - validate
    - ignore
    default: validate
    type: str
    vars:
    - name: ansible_psrp_cert_validation
  ca_cert:
    description:
    - The path to a PEM certificate chain to use when validating the server's
      certificate.
    - This value is ignored if O(cert_validation) is set to V(ignore).
    type: path
    vars:
    - name: ansible_psrp_cert_trust_path
    - name: ansible_psrp_ca_cert
    aliases: [ cert_trust_path ]
  connection_timeout:
    description:
    - The connection timeout for making the request to the remote host.
    - This is measured in seconds.
    type: int
    vars:
    - name: ansible_psrp_connection_timeout
    default: 30
  read_timeout:
    description:
    - The read timeout for receiving data from the remote host.
    - This value must always be greater than O(operation_timeout).
    - This option requires pypsrp >= 0.3.
    - This is measured in seconds.
    type: int
    vars:
    - name: ansible_psrp_read_timeout
    default: 30
    version_added: '2.8'
  reconnection_retries:
    description:
    - The number of retries on connection errors.
    type: int
    vars:
    - name: ansible_psrp_reconnection_retries
    default: 0
    version_added: '2.8'
  reconnection_backoff:
    description:
    - The backoff time to use in between reconnection attempts.
      (First sleeps X, then sleeps 2*X, then sleeps 4*X, ...)
    - This is measured in seconds.
    - The C(ansible_psrp_reconnection_backoff) variable was added in Ansible
      2.9.
    type: int
    vars:
    - name: ansible_psrp_connection_backoff
    - name: ansible_psrp_reconnection_backoff
    default: 2
    version_added: '2.8'
  message_encryption:
    description:
    - Controls the message encryption settings, this is different from TLS
      encryption when O(protocol) is V(https).
    - Only the auth protocols V(negotiate), V(kerberos), V(ntlm), and
      V(credssp) can do message encryption. The other authentication protocols
      only support encryption when V(protocol) is set to V(https).
    - V(auto) means means message encryption is only used when not using
      TLS/HTTPS.
    - V(always) is the same as V(auto) but message encryption is always used
      even when running over TLS/HTTPS.
    - V(never) disables any encryption checks that are in place when running
      over HTTP and disables any authentication encryption processes.
    type: str
    vars:
    - name: ansible_psrp_message_encryption
    choices:
    - auto
    - always
    - never
    default: auto
  proxy:
    description:
    - Set the proxy URL to use when connecting to the remote host.
    vars:
    - name: ansible_psrp_proxy
    type: str
  ignore_proxy:
    description:
    - Will disable any environment proxy settings and connect directly to the
      remote host.
    - This option is ignored if O(proxy) is set.
    vars:
    - name: ansible_psrp_ignore_proxy
    type: bool
    default: false

  # auth options
  certificate_key_pem:
    description:
    - The local path to an X509 certificate key to use with certificate auth.
    type: path
    vars:
    - name: ansible_psrp_certificate_key_pem
  certificate_pem:
    description:
    - The local path to an X509 certificate to use with certificate auth.
    type: path
    vars:
    - name: ansible_psrp_certificate_pem
  credssp_auth_mechanism:
    description:
    - The sub authentication mechanism to use with CredSSP auth.
    - When V(auto), both Kerberos and NTLM is attempted with kerberos being
      preferred.
    type: str
    choices:
    - auto
    - kerberos
    - ntlm
    default: auto
    vars:
    - name: ansible_psrp_credssp_auth_mechanism
  credssp_disable_tlsv1_2:
    description:
    - Disables the use of TLSv1.2 on the CredSSP authentication channel.
    - This should not be set to V(yes) unless dealing with a host that does not
      have TLSv1.2.
    default: false
    type: bool
    vars:
    - name: ansible_psrp_credssp_disable_tlsv1_2
  credssp_minimum_version:
    description:
    - The minimum CredSSP server authentication version that will be accepted.
    - Set to V(5) to ensure the server has been patched and is not vulnerable
      to CVE 2018-0886.
    default: 2
    type: int
    vars:
    - name: ansible_psrp_credssp_minimum_version
  negotiate_delegate:
    description:
    - Allow the remote user the ability to delegate it's credentials to another
      server, i.e. credential delegation.
    - Only valid when Kerberos was the negotiated auth or was explicitly set as
      the authentication.
    - Ignored when NTLM was the negotiated auth.
    type: bool
    vars:
    - name: ansible_psrp_negotiate_delegate
  negotiate_hostname_override:
    description:
    - Override the remote hostname when searching for the host in the Kerberos
      lookup.
    - This allows Ansible to connect over IP but authenticate with the remote
      server using it's DNS name.
    - Only valid when Kerberos was the negotiated auth or was explicitly set as
      the authentication.
    - Ignored when NTLM was the negotiated auth.
    type: str
    vars:
    - name: ansible_psrp_negotiate_hostname_override
  negotiate_send_cbt:
    description:
    - Send the Channel Binding Token (CBT) structure when authenticating.
    - CBT is used to provide extra protection against Man in the Middle C(MitM)
      attacks by binding the outer transport channel to the auth channel.
    - CBT is not used when using just C(HTTP), only C(HTTPS).
    default: true
    type: bool
    vars:
    - name: ansible_psrp_negotiate_send_cbt
  negotiate_service:
    description:
    - Override the service part of the SPN used during Kerberos authentication.
    - Only valid when Kerberos was the negotiated auth or was explicitly set as
      the authentication.
    - Ignored when NTLM was the negotiated auth.
    default: WSMAN
    type: str
    vars:
    - name: ansible_psrp_negotiate_service

  # protocol options
  operation_timeout:
    description:
    - Sets the WSMan timeout for each operation.
    - This is measured in seconds.
    - This should not exceed the value for O(connection_timeout).
    type: int
    vars:
    - name: ansible_psrp_operation_timeout
    default: 20
  max_envelope_size:
    description:
    - Sets the maximum size of each WSMan message sent to the remote host.
    - This is measured in bytes.
    - Defaults to C(150KiB) for compatibility with older hosts.
    type: int
    vars:
    - name: ansible_psrp_max_envelope_size
    default: 153600
  configuration_name:
    description:
    - The name of the PowerShell configuration endpoint to connect to.
    type: str
    vars:
    - name: ansible_psrp_configuration_name
    default: Microsoft.PowerShell
"""

import base64
import json
import logging
import os
import shlex
import typing as t

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.executor.powershell.module_manifest import _bootstrap_powershell_script
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import ShellModule as PowerShellPlugin
from ansible.plugins.shell.powershell import _common_args
from ansible.utils.display import Display
from ansible.utils.hashing import sha1

HAS_PYPSRP = True
PYPSRP_IMP_ERR = None
try:
    from pypsrp.complex_objects import GenericComplexObject, PSInvocationState, RunspacePoolState
    from pypsrp.exceptions import AuthenticationError, WinRMError
    from pypsrp.host import PSHost, PSHostUserInterface
    from pypsrp.powershell import PowerShell, RunspacePool
    from pypsrp.wsman import WSMan
    from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
except ImportError as err:
    HAS_PYPSRP = False
    PYPSRP_IMP_ERR = err

display = Display()


class Connection(ConnectionBase):

    transport = 'psrp'
    module_implementation_preferences = ('.ps1', '.exe', '')
    allow_executable = False
    has_pipelining = True

    # Satisfies mypy as this connection only ever runs with this plugin
    _shell: PowerShellPlugin

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.always_pipeline_modules = True
        self.has_native_async = True

        self.runspace: RunspacePool | None = None
        self.host: PSHost | None = None
        self._last_pipeline: PowerShell | None = None

        self._shell_type = 'powershell'
        super(Connection, self).__init__(*args, **kwargs)

        if not C.DEFAULT_DEBUG:
            logging.getLogger('pypsrp').setLevel(logging.WARNING)
            logging.getLogger('requests_credssp').setLevel(logging.INFO)
            logging.getLogger('urllib3').setLevel(logging.INFO)

    def _connect(self) -> Connection:
        if not HAS_PYPSRP:
            raise AnsibleError("pypsrp or dependencies are not installed: %s"
                               % to_native(PYPSRP_IMP_ERR))
        super(Connection, self)._connect()
        self._build_kwargs()
        display.vvv("ESTABLISH PSRP CONNECTION FOR USER: %s ON PORT %s TO %s" %
                    (self._psrp_user, self._psrp_port, self._psrp_host),
                    host=self._psrp_host)

        if not self.runspace:
            connection = WSMan(**self._psrp_conn_kwargs)

            # create our pseudo host to capture the exit code and host output
            host_ui = PSHostUserInterface()
            self.host = PSHost(None, None, False, "Ansible PSRP Host", None,
                               host_ui, None)

            self.runspace = RunspacePool(
                connection, host=self.host,
                configuration_name=self._psrp_configuration_name
            )
            display.vvvvv(
                "PSRP OPEN RUNSPACE: auth=%s configuration=%s endpoint=%s" %
                (self._psrp_auth, self._psrp_configuration_name,
                 connection.transport.endpoint), host=self._psrp_host
            )
            try:
                self.runspace.open()
            except AuthenticationError as e:
                raise AnsibleConnectionFailure("failed to authenticate with "
                                               "the server: %s" % to_native(e))
            except WinRMError as e:
                raise AnsibleConnectionFailure(
                    "psrp connection failure during runspace open: %s"
                    % to_native(e)
                )
            except (ConnectionError, ConnectTimeout) as e:
                raise AnsibleConnectionFailure(
                    "Failed to connect to the host via PSRP: %s"
                    % to_native(e)
                )

            self._connected = True
            self._last_pipeline = None
        return self

    def reset(self) -> None:
        if not self._connected:
            self.runspace = None
            return

        # Try out best to ensure the runspace is closed to free up server side resources
        try:
            self.close()
        except Exception as e:
            # There's a good chance the connection was already closed so just log the error and move on
            display.debug("PSRP reset - failed to closed runspace: %s" % to_text(e))

        display.vvvvv("PSRP: Reset Connection", host=self._psrp_host)
        self.runspace = None
        self._connect()

    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        super(Connection, self).exec_command(cmd, in_data=in_data,
                                             sudoable=sudoable)

        pwsh_in_data: bytes | str | None = None
        script_args: list[str] | None = None

        common_args_prefix = " ".join(_common_args)
        if cmd.startswith(f"{common_args_prefix} -EncodedCommand"):
            # This is a PowerShell script encoded by the shell plugin, we will
            # decode the script and execute it in the runspace instead of
            # starting a new interpreter to save on time
            b_command = base64.b64decode(cmd.split(" ")[-1])
            script = to_text(b_command, 'utf-16-le')
            pwsh_in_data = to_text(in_data, errors="surrogate_or_strict", nonstring="passthru")

            if pwsh_in_data and isinstance(pwsh_in_data, str) and pwsh_in_data.startswith("#!"):
                # ANSIBALLZ wrapper, we need to get the interpreter and execute
                # that as the script - note this won't work as basic.py relies
                # on packages not available on Windows, once fixed we can enable
                # this path
                interpreter = to_native(pwsh_in_data.splitlines()[0][2:])
                # script = "$input | &'%s' -" % interpreter
                raise AnsibleError("cannot run the interpreter '%s' on the psrp "
                                   "connection plugin" % interpreter)

            # call build_module_command to get the bootstrap wrapper text
            bootstrap_wrapper = self._shell.build_module_command('', '', '')
            if bootstrap_wrapper == cmd:
                # Do not display to the user each invocation of the bootstrap wrapper
                display.vvv("PSRP: EXEC (via pipeline wrapper)")
            else:
                display.vvv("PSRP: EXEC %s" % script, host=self._psrp_host)

        elif cmd.startswith(f"{common_args_prefix} -File "):  # trailing space is on purpose
            # Used when executing a script file, we will execute it in the runspace process
            # instead on a new subprocess
            script = 'param([string]$Path, [Parameter(ValueFromRemainingArguments)][string[]]$ScriptArgs) & $Path @ScriptArgs'

            # Using shlex isn't perfect but it's good enough.
            cmd = cmd[len(common_args_prefix) + 7:]
            script_args = shlex.split(cmd)
            display.vvv(f"PSRP: EXEC {cmd}")

        else:
            # In other cases we want to execute the cmd as the script. We add on the 'exit $LASTEXITCODE' to ensure the
            # rc is propagated back to the connection plugin.
            script = to_text(u"%s\nexit $LASTEXITCODE" % cmd)
            pwsh_in_data = in_data
            display.vvv(u"PSRP: EXEC %s" % script, host=self._psrp_host)

        try:
            rc, stdout, stderr = self._exec_psrp_script(
                script=script,
                input_data=pwsh_in_data.splitlines() if pwsh_in_data else None,
                arguments=script_args,
            )
        except ReadTimeout as e:
            raise AnsibleConnectionFailure(
                "HTTP read timeout during PSRP script execution"
            ) from e
        return rc, stdout, stderr

    def put_file(self, in_path: str, out_path: str) -> None:
        super(Connection, self).put_file(in_path, out_path)

        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._psrp_host)

        script, in_data = _bootstrap_powershell_script('psrp_put_file.ps1', {
            'Path': out_path,
        }, has_input=True)

        # Get the buffer size of each fragment to send, subtract 82 for the fragment, message, and other header info
        # fields that PSRP adds. Adjust to size of the base64 encoded bytes length.
        buffer_size = int((self.runspace.connection.max_payload_size - 82) / 4 * 3)

        sha1_hash = sha1()

        b_in_path = to_bytes(in_path, errors='surrogate_or_strict')
        if not os.path.exists(b_in_path):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % to_native(in_path))

        def read_gen():
            yield from in_data.decode().splitlines()

            offset = 0

            with open(b_in_path, 'rb') as src_fd:
                for b_data in iter((lambda: src_fd.read(buffer_size)), b""):
                    data_len = len(b_data)
                    offset += data_len
                    sha1_hash.update(b_data)

                    # PSRP technically supports sending raw bytes but that method requires a larger CLIXML message.
                    # Sending base64 is still more efficient here.
                    display.vvvvv("PSRP PUT %s to %s (offset=%d, size=%d" % (in_path, out_path, offset, data_len),
                                  host=self._psrp_host)
                    b64_data = base64.b64encode(b_data)
                    yield [to_text(b64_data)]

                if offset == 0:  # empty file
                    yield [""]

        rc, stdout, stderr = self._exec_psrp_script(script, read_gen())

        if rc != 0:
            raise AnsibleError(to_native(stderr))

        put_output = json.loads(to_text(stdout))
        local_sha1 = sha1_hash.hexdigest()
        remote_sha1 = put_output.get("sha1")

        if not remote_sha1:
            raise AnsibleError("Remote sha1 was not returned, stdout: '%s', stderr: '%s'"
                               % (to_native(stdout), to_native(stderr)))

        if not remote_sha1 == local_sha1:
            raise AnsibleError("Remote sha1 hash %s does not match local hash %s"
                               % (to_native(remote_sha1), to_native(local_sha1)))

    def fetch_file(self, in_path: str, out_path: str) -> None:
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path),
                    host=self._psrp_host)

        out_path = out_path.replace('\\', '/')
        b_out_path = to_bytes(out_path, errors='surrogate_or_strict')

        # because we are dealing with base64 data we need to get the max size
        # of the bytes that the base64 size would equal
        max_b64_size = int(self.runspace.connection.max_payload_size -
                           (self.runspace.connection.max_payload_size / 4 * 3))
        buffer_size = max_b64_size - (max_b64_size % 1024)

        script, in_data = _bootstrap_powershell_script('psrp_fetch_file.ps1', {
            'Path': in_path,
            'BufferSize': buffer_size,
        })

        ps = PowerShell(self.runspace)
        ps.add_script(script)
        ps.begin_invoke(in_data.decode().splitlines())

        # Call poll once to get the first output telling us if it's a file/dir/failure
        ps.poll_invoke()

        if ps.output:
            if ps.output.pop(0) == '[DIR]':
                # to be consistent with other connection plugins, we assume the caller has created the target dir
                return

            with open(b_out_path, 'wb') as out_file:
                while True:
                    while ps.output:
                        data = base64.b64decode(ps.output.pop(0))
                        out_file.write(data)

                    if ps.state == PSInvocationState.RUNNING:
                        ps.poll_invoke()
                    else:
                        break

        ps.end_invoke()
        rc, stdout, stderr = self._parse_pipeline_result(ps)
        if rc != 0:
            raise AnsibleError(f"failed to transfer file to '{out_path}': {to_text(stderr)}")

    def close(self) -> None:
        if self.runspace and self.runspace.state == RunspacePoolState.OPENED:
            display.vvvvv("PSRP CLOSE RUNSPACE: %s" % (self.runspace.id),
                          host=self._psrp_host)
            self.runspace.close()
        self.runspace = None
        self._connected = False
        self._last_pipeline = None

    def _build_kwargs(self) -> None:
        self._psrp_host = self.get_option('remote_addr')
        self._psrp_user = self.get_option('remote_user')

        protocol = self.get_option('protocol')
        port = self.get_option('port')
        if protocol is None and port is None:
            protocol = 'https'
            port = 5986
        elif protocol is None:
            protocol = 'https' if int(port) != 5985 else 'http'
        elif port is None:
            port = 5986 if protocol == 'https' else 5985

        self._psrp_port = int(port)
        self._psrp_auth = self.get_option('auth')
        self._psrp_configuration_name = self.get_option('configuration_name')

        # cert validation can either be a bool or a path to the cert
        cert_validation = self.get_option('cert_validation')
        cert_trust_path = self.get_option('ca_cert')
        if cert_validation == 'ignore':
            psrp_cert_validation = False
        elif cert_trust_path is not None:
            psrp_cert_validation = cert_trust_path
        else:
            psrp_cert_validation = True

        self._psrp_conn_kwargs = dict(
            server=self._psrp_host,
            port=self._psrp_port,
            username=self._psrp_user,
            password=self.get_option('remote_password'),
            ssl=protocol == 'https',
            path=self.get_option('path'),
            auth=self._psrp_auth,
            cert_validation=psrp_cert_validation,
            connection_timeout=self.get_option('connection_timeout'),
            encryption=self.get_option('message_encryption'),
            proxy=self.get_option('proxy'),
            no_proxy=boolean(self.get_option('ignore_proxy')),
            max_envelope_size=self.get_option('max_envelope_size'),
            operation_timeout=self.get_option('operation_timeout'),
            read_timeout=self.get_option('read_timeout'),
            reconnection_retries=self.get_option('reconnection_retries'),
            reconnection_backoff=float(self.get_option('reconnection_backoff')),
            certificate_key_pem=self.get_option('certificate_key_pem'),
            certificate_pem=self.get_option('certificate_pem'),
            credssp_auth_mechanism=self.get_option('credssp_auth_mechanism'),
            credssp_disable_tlsv1_2=self.get_option('credssp_disable_tlsv1_2'),
            credssp_minimum_version=self.get_option('credssp_minimum_version'),
            negotiate_send_cbt=self.get_option('negotiate_send_cbt'),
            negotiate_delegate=self.get_option('negotiate_delegate'),
            negotiate_hostname_override=self.get_option('negotiate_hostname_override'),
            negotiate_service=self.get_option('negotiate_service'),
        )

    def _exec_psrp_script(
        self,
        script: str,
        input_data: bytes | str | t.Iterable | None = None,
        use_local_scope: bool = True,
        arguments: t.Iterable[t.Any] | None = None,
    ) -> tuple[int, bytes, bytes]:
        # Check if there's a command on the current pipeline that still needs to be closed.
        if self._last_pipeline:
            # Current pypsrp versions raise an exception if the current state was not RUNNING. We manually set it so we
            # can call stop without any issues.
            self._last_pipeline.state = PSInvocationState.RUNNING
            self._last_pipeline.stop()
            self._last_pipeline = None

        ps = PowerShell(self.runspace)
        ps.add_script(script, use_local_scope=use_local_scope)
        if arguments:
            for arg in arguments:
                ps.add_argument(arg)

        ps.invoke(input=input_data)

        rc, stdout, stderr = self._parse_pipeline_result(ps)

        # We should really call .stop() on all pipelines that are run to decrement the concurrent command counter on
        # PSSession but that involves another round trip and is done when the runspace is closed. We instead store the
        # last pipeline which is closed if another command is run on the runspace.
        self._last_pipeline = ps

        return rc, stdout, stderr

    def _parse_pipeline_result(self, pipeline: PowerShell) -> tuple[int, bytes, bytes]:
        """
        PSRP doesn't have the same concept as other protocols with its output.
        We need some extra logic to convert the pipeline streams and host
        output into the format that Ansible understands.

        :param pipeline: The finished PowerShell pipeline that invoked our
            commands
        :return: rc, stdout, stderr based on the pipeline output
        """
        # we try and get the rc from our host implementation, this is set if
        # exit or $host.SetShouldExit() is called in our pipeline, if not we
        # set to 0 if the pipeline had not errors and 1 if it did
        rc = self.host.rc or (1 if pipeline.had_errors else 0)

        # TODO: figure out a better way of merging this with the host output
        stdout_list = []
        for output in pipeline.output:
            # Not all pipeline outputs are a string or contain a __str__ value,
            # we will create our own output based on the properties of the
            # complex object if that is the case.
            if isinstance(output, GenericComplexObject) and output.to_string is None:
                obj_lines = output.property_sets
                for key, value in output.adapted_properties.items():
                    obj_lines.append(u"%s: %s" % (key, value))
                for key, value in output.extended_properties.items():
                    obj_lines.append(u"%s: %s" % (key, value))
                output_msg = u"\n".join(obj_lines)
            else:
                output_msg = to_text(output, nonstring='simplerepr')

            stdout_list.append(output_msg)

        if len(self.host.ui.stdout) > 0:
            stdout_list += self.host.ui.stdout
        stdout = u"\r\n".join(stdout_list)

        stderr_list = []
        for error in pipeline.streams.error:
            # the error record is not as fully fleshed out like we usually get
            # in PS, we will manually create it here
            # NativeCommandError and NativeCommandErrorMessage are special
            # cases used for stderr from a subprocess, we will just print the
            # error message
            if error.fq_error == 'NativeCommandErrorMessage' and not error.target_name:
                # This can be removed once Server 2016 is EOL and no longer
                # supported. PS 5.1 on 2016 will emit 1 error record under
                # NativeCommandError being the first line, subsequent records
                # are the raw stderr up to 4096 chars. Each entry is the raw
                # stderr value without any newlines appended so we just use the
                # value as is. We know it's 2016 as the target_name is empty in
                # this scenario.
                stderr_list.append(str(error))
                continue
            elif error.fq_error in ['NativeCommandError', 'NativeCommandErrorMessage']:
                stderr_list.append(f"{error}\r\n")
                continue

            command_name = "%s : " % error.command_name if error.command_name else ''
            position = "%s\r\n" % error.invocation_position_message if error.invocation_position_message else ''
            error_msg = "%s%s\r\n%s" \
                        "    + CategoryInfo          : %s\r\n" \
                        "    + FullyQualifiedErrorId : %s" \
                        % (command_name, str(error), position,
                           error.message, error.fq_error)
            stacktrace = error.script_stacktrace
            if display.verbosity >= 3 and stacktrace is not None:
                error_msg += "\r\nStackTrace:\r\n%s" % stacktrace
            stderr_list.append(f"{error_msg}\r\n")

        if len(self.host.ui.stderr) > 0:
            stderr_list += self.host.ui.stderr
        stderr = "".join([to_text(o) for o in stderr_list])

        display.vvvvv("PSRP RC: %d" % rc, host=self._psrp_host)
        display.vvvvv("PSRP STDOUT: %s" % stdout, host=self._psrp_host)
        display.vvvvv("PSRP STDERR: %s" % stderr, host=self._psrp_host)

        # reset the host back output back to defaults, needed if running
        # multiple pipelines on the same RunspacePool
        self.host.rc = 0
        self.host.ui.stdout = []
        self.host.ui.stderr = []

        return rc, to_bytes(stdout, encoding='utf-8'), to_bytes(stderr, encoding='utf-8')

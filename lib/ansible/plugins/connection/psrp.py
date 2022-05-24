# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
author: Ansible Core Team
name: psrp
short_description: Run tasks over Microsoft PowerShell Remoting Protocol
description:
- Run commands or put/fetch on a target via PSRP (WinRM plugin)
- This is similar to the I(winrm) connection plugin which uses the same
  underlying transport but instead runs in a PowerShell interpreter.
version_added: "2.7"
requirements:
- pypsrp>=0.4.0 (Python library)
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
    description: Authentication password for the C(remote_user). Can be supplied as CLI option.
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
    - Default is C(5986) if I(protocol) is not defined or is C(https),
      otherwise the port is C(5985).
    type: int
    vars:
    - name: ansible_port
    - name: ansible_psrp_port
    keyword:
    - name: port
  protocol:
    description:
    - Set the protocol to use for the connection.
    - Default is C(https) if I(port) is not defined or I(port) is not C(5985).
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
    - The default, C(negotiate), will attempt to use C(Kerberos) if it is
      available and fall back to C(NTLM) if it isn't.
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
    - Set to C(ignore) to not validate any certificates.
    - I(ca_cert) can be set to the path of a PEM certificate chain to
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
    - This value is ignored if I(cert_validation) is set to C(ignore).
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
    - This value must always be greater than I(operation_timeout).
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
      encryption when I(ansible_psrp_protocol) is C(https).
    - Only the auth protocols C(negotiate), C(kerberos), C(ntlm), and
      C(credssp) can do message encryption. The other authentication protocols
      only support encryption when C(protocol) is set to C(https).
    - C(auto) means means message encryption is only used when not using
      TLS/HTTPS.
    - C(always) is the same as C(auto) but message encryption is always used
      even when running over TLS/HTTPS.
    - C(never) disables any encryption checks that are in place when running
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
    - This option is ignored if C(proxy) is set.
    vars:
    - name: ansible_psrp_ignore_proxy
    type: bool
    default: 'no'

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
    - When C(auto), both Kerberos and NTLM is attempted with kerberos being
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
    - This should not be set to C(yes) unless dealing with a host that does not
      have TLSv1.2.
    default: no
    type: bool
    vars:
    - name: ansible_psrp_credssp_disable_tlsv1_2
  credssp_minimum_version:
    description:
    - The minimum CredSSP server authentication version that will be accepted.
    - Set to C(5) to ensure the server has been patched and is not vulnerable
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
    default: yes
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
    - This should not exceed the value for C(connection_timeout).
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

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import _common_args
from ansible.utils.display import Display
from ansible.utils.hashing import sha1

HAS_PYPSRP = True
PYPSRP_IMP_ERR = None
try:
    import pypsrp
    from pypsrp.complex_objects import GenericComplexObject, PSInvocationState, RunspacePoolState
    from pypsrp.exceptions import AuthenticationError, WinRMError
    from pypsrp.host import PSHost, PSHostUserInterface
    from pypsrp.powershell import PowerShell, RunspacePool
    from pypsrp.wsman import WSMan, AUTH_KWARGS
    from requests.exceptions import ConnectionError, ConnectTimeout
except ImportError as err:
    HAS_PYPSRP = False
    PYPSRP_IMP_ERR = err

display = Display()


class Connection(ConnectionBase):

    transport = 'psrp'
    module_implementation_preferences = ('.ps1', '.exe', '')
    allow_executable = False
    has_pipelining = True
    allow_extras = True

    def __init__(self, *args, **kwargs):
        self.always_pipeline_modules = True
        self.has_native_async = True

        self.runspace = None
        self.host = None
        self._last_pipeline = False

        self._shell_type = 'powershell'
        super(Connection, self).__init__(*args, **kwargs)

        if not C.DEFAULT_DEBUG:
            logging.getLogger('pypsrp').setLevel(logging.WARNING)
            logging.getLogger('requests_credssp').setLevel(logging.INFO)
            logging.getLogger('urllib3').setLevel(logging.INFO)

    def _connect(self):
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

    def reset(self):
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

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super(Connection, self).exec_command(cmd, in_data=in_data,
                                             sudoable=sudoable)

        if cmd.startswith(" ".join(_common_args) + " -EncodedCommand"):
            # This is a PowerShell script encoded by the shell plugin, we will
            # decode the script and execute it in the runspace instead of
            # starting a new interpreter to save on time
            b_command = base64.b64decode(cmd.split(" ")[-1])
            script = to_text(b_command, 'utf-16-le')
            in_data = to_text(in_data, errors="surrogate_or_strict", nonstring="passthru")

            if in_data and in_data.startswith(u"#!"):
                # ANSIBALLZ wrapper, we need to get the interpreter and execute
                # that as the script - note this won't work as basic.py relies
                # on packages not available on Windows, once fixed we can enable
                # this path
                interpreter = to_native(in_data.splitlines()[0][2:])
                # script = "$input | &'%s' -" % interpreter
                # in_data = to_text(in_data)
                raise AnsibleError("cannot run the interpreter '%s' on the psrp "
                                   "connection plugin" % interpreter)

            # call build_module_command to get the bootstrap wrapper text
            bootstrap_wrapper = self._shell.build_module_command('', '', '')
            if bootstrap_wrapper == cmd:
                # Do not display to the user each invocation of the bootstrap wrapper
                display.vvv("PSRP: EXEC (via pipeline wrapper)")
            else:
                display.vvv("PSRP: EXEC %s" % script, host=self._psrp_host)
        else:
            # In other cases we want to execute the cmd as the script. We add on the 'exit $LASTEXITCODE' to ensure the
            # rc is propagated back to the connection plugin.
            script = to_text(u"%s\nexit $LASTEXITCODE" % cmd)
            display.vvv(u"PSRP: EXEC %s" % script, host=self._psrp_host)

        rc, stdout, stderr = self._exec_psrp_script(script, in_data)
        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)

        out_path = self._shell._unquote(out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._psrp_host)

        copy_script = '''begin {
    $ErrorActionPreference = "Stop"
    $WarningPreference = "Continue"
    $path = $MyInvocation.UnboundArguments[0]
    $fd = [System.IO.File]::Create($path)
    $algo = [System.Security.Cryptography.SHA1CryptoServiceProvider]::Create()
    $bytes = @()

    $bindingFlags = [System.Reflection.BindingFlags]'NonPublic, Instance'
    Function Get-Property {
        <#
        .SYNOPSIS
        Gets the private/internal property specified of the object passed in.
        #>
        Param (
            [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
            [System.Object]
            $Object,

            [Parameter(Mandatory=$true, Position=1)]
            [System.String]
            $Name
        )

        $Object.GetType().GetProperty($Name, $bindingFlags).GetValue($Object, $null)
    }

    Function Set-Property {
        <#
        .SYNOPSIS
        Sets the private/internal property specified on the object passed in.
        #>
        Param (
            [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
            [System.Object]
            $Object,

            [Parameter(Mandatory=$true, Position=1)]
            [System.String]
            $Name,

            [Parameter(Mandatory=$true, Position=2)]
            [AllowNull()]
            [System.Object]
            $Value
        )

        $Object.GetType().GetProperty($Name, $bindingFlags).SetValue($Object, $Value, $null)
    }

    Function Get-Field {
        <#
        .SYNOPSIS
        Gets the private/internal field specified of the object passed in.
        #>
        Param (
            [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
            [System.Object]
            $Object,

            [Parameter(Mandatory=$true, Position=1)]
            [System.String]
            $Name
        )

        $Object.GetType().GetField($Name, $bindingFlags).GetValue($Object)
    }

    # MaximumAllowedMemory is required to be set to so we can send input data that exceeds the limit on a PS
    # Runspace. We use reflection to access/set this property as it is not accessible publicly. This is not ideal
    # but works on all PowerShell versions I've tested with. We originally used WinRS to send the raw bytes to the
    # host but this falls flat if someone is using a custom PS configuration name so this is a workaround. This
    # isn't required for smaller files so if it fails we ignore the error and hope it wasn't needed.
    # https://github.com/PowerShell/PowerShell/blob/c8e72d1e664b1ee04a14f226adf655cced24e5f0/src/System.Management.Automation/engine/serialization.cs#L325
    try {
        $Host | Get-Property 'ExternalHost' | `
            Get-Field '_transportManager' | `
            Get-Property 'Fragmentor' | `
            Get-Property 'DeserializationContext' | `
            Set-Property 'MaximumAllowedMemory' $null
    } catch {}
}
process {
    $bytes = [System.Convert]::FromBase64String($input)
    $algo.TransformBlock($bytes, 0, $bytes.Length, $bytes, 0) > $null
    $fd.Write($bytes, 0, $bytes.Length)
}
end {
    $fd.Close()

    $algo.TransformFinalBlock($bytes, 0, 0) > $null
    $hash = [System.BitConverter]::ToString($algo.Hash).Replace('-', '').ToLowerInvariant()
    Write-Output -InputObject "{`"sha1`":`"$hash`"}"
}
'''

        # Get the buffer size of each fragment to send, subtract 82 for the fragment, message, and other header info
        # fields that PSRP adds. Adjust to size of the base64 encoded bytes length.
        buffer_size = int((self.runspace.connection.max_payload_size - 82) / 4 * 3)

        sha1_hash = sha1()

        b_in_path = to_bytes(in_path, errors='surrogate_or_strict')
        if not os.path.exists(b_in_path):
            raise AnsibleFileNotFound('file or module does not exist: "%s"' % to_native(in_path))

        def read_gen():
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

        rc, stdout, stderr = self._exec_psrp_script(copy_script, read_gen(), arguments=[out_path])

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

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path),
                    host=self._psrp_host)

        in_path = self._shell._unquote(in_path)
        out_path = out_path.replace('\\', '/')

        # because we are dealing with base64 data we need to get the max size
        # of the bytes that the base64 size would equal
        max_b64_size = int(self.runspace.connection.max_payload_size -
                           (self.runspace.connection.max_payload_size / 4 * 3))
        buffer_size = max_b64_size - (max_b64_size % 1024)

        # setup the file stream with read only mode
        setup_script = '''$ErrorActionPreference = "Stop"
$path = '%s'

if (Test-Path -Path $path -PathType Leaf) {
    $fs = New-Object -TypeName System.IO.FileStream -ArgumentList @(
        $path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read
    )
    $buffer_size = %d
} elseif (Test-Path -Path $path -PathType Container) {
    Write-Output -InputObject "[DIR]"
} else {
    Write-Error -Message "$path does not exist"
    $host.SetShouldExit(1)
}''' % (self._shell._escape(in_path), buffer_size)

        # read the file stream at the offset and return the b64 string
        read_script = '''$ErrorActionPreference = "Stop"
$fs.Seek(%d, [System.IO.SeekOrigin]::Begin) > $null
$buffer = New-Object -TypeName byte[] -ArgumentList $buffer_size
$bytes_read = $fs.Read($buffer, 0, $buffer_size)

if ($bytes_read -gt 0) {
    $bytes = $buffer[0..($bytes_read - 1)]
    Write-Output -InputObject ([System.Convert]::ToBase64String($bytes))
}'''

        # need to run the setup script outside of the local scope so the
        # file stream stays active between fetch operations
        rc, stdout, stderr = self._exec_psrp_script(setup_script,
                                                    use_local_scope=False)
        if rc != 0:
            raise AnsibleError("failed to setup file stream for fetch '%s': %s"
                               % (out_path, to_native(stderr)))
        elif stdout.strip() == '[DIR]':
            # to be consistent with other connection plugins, we assume the caller has created the target dir
            return

        b_out_path = to_bytes(out_path, errors='surrogate_or_strict')
        # to be consistent with other connection plugins, we assume the caller has created the target dir
        offset = 0
        with open(b_out_path, 'wb') as out_file:
            while True:
                display.vvvvv("PSRP FETCH %s to %s (offset=%d" %
                              (in_path, out_path, offset), host=self._psrp_host)
                rc, stdout, stderr = self._exec_psrp_script(read_script % offset)
                if rc != 0:
                    raise AnsibleError("failed to transfer file to '%s': %s"
                                       % (out_path, to_native(stderr)))

                data = base64.b64decode(stdout.strip())
                out_file.write(data)
                if len(data) < buffer_size:
                    break
                offset += len(data)

            rc, stdout, stderr = self._exec_psrp_script("$fs.Close()")
            if rc != 0:
                display.warning("failed to close remote file stream of file "
                                "'%s': %s" % (in_path, to_native(stderr)))

    def close(self):
        if self.runspace and self.runspace.state == RunspacePoolState.OPENED:
            display.vvvvv("PSRP CLOSE RUNSPACE: %s" % (self.runspace.id),
                          host=self._psrp_host)
            self.runspace.close()
        self.runspace = None
        self._connected = False
        self._last_pipeline = None

    def _build_kwargs(self):
        self._psrp_host = self.get_option('remote_addr')
        self._psrp_user = self.get_option('remote_user')
        self._psrp_pass = self.get_option('remote_password')

        protocol = self.get_option('protocol')
        port = self.get_option('port')
        if protocol is None and port is None:
            protocol = 'https'
            port = 5986
        elif protocol is None:
            protocol = 'https' if int(port) != 5985 else 'http'
        elif port is None:
            port = 5986 if protocol == 'https' else 5985

        self._psrp_protocol = protocol
        self._psrp_port = int(port)

        self._psrp_path = self.get_option('path')
        self._psrp_auth = self.get_option('auth')
        # cert validation can either be a bool or a path to the cert
        cert_validation = self.get_option('cert_validation')
        cert_trust_path = self.get_option('ca_cert')
        if cert_validation == 'ignore':
            self._psrp_cert_validation = False
        elif cert_trust_path is not None:
            self._psrp_cert_validation = cert_trust_path
        else:
            self._psrp_cert_validation = True

        self._psrp_connection_timeout = self.get_option('connection_timeout')  # Can be None
        self._psrp_read_timeout = self.get_option('read_timeout')  # Can be None
        self._psrp_message_encryption = self.get_option('message_encryption')
        self._psrp_proxy = self.get_option('proxy')
        self._psrp_ignore_proxy = boolean(self.get_option('ignore_proxy'))
        self._psrp_operation_timeout = int(self.get_option('operation_timeout'))
        self._psrp_max_envelope_size = int(self.get_option('max_envelope_size'))
        self._psrp_configuration_name = self.get_option('configuration_name')
        self._psrp_reconnection_retries = int(self.get_option('reconnection_retries'))
        self._psrp_reconnection_backoff = float(self.get_option('reconnection_backoff'))

        self._psrp_certificate_key_pem = self.get_option('certificate_key_pem')
        self._psrp_certificate_pem = self.get_option('certificate_pem')
        self._psrp_credssp_auth_mechanism = self.get_option('credssp_auth_mechanism')
        self._psrp_credssp_disable_tlsv1_2 = self.get_option('credssp_disable_tlsv1_2')
        self._psrp_credssp_minimum_version = self.get_option('credssp_minimum_version')
        self._psrp_negotiate_send_cbt = self.get_option('negotiate_send_cbt')
        self._psrp_negotiate_delegate = self.get_option('negotiate_delegate')
        self._psrp_negotiate_hostname_override = self.get_option('negotiate_hostname_override')
        self._psrp_negotiate_service = self.get_option('negotiate_service')

        supported_args = []
        for auth_kwarg in AUTH_KWARGS.values():
            supported_args.extend(auth_kwarg)
        extra_args = {v.replace('ansible_psrp_', '') for v in self.get_option('_extras')}
        unsupported_args = extra_args.difference(supported_args)

        for arg in unsupported_args:
            display.warning("ansible_psrp_%s is unsupported by the current "
                            "psrp version installed" % arg)

        self._psrp_conn_kwargs = dict(
            server=self._psrp_host, port=self._psrp_port,
            username=self._psrp_user, password=self._psrp_pass,
            ssl=self._psrp_protocol == 'https', path=self._psrp_path,
            auth=self._psrp_auth, cert_validation=self._psrp_cert_validation,
            connection_timeout=self._psrp_connection_timeout,
            encryption=self._psrp_message_encryption, proxy=self._psrp_proxy,
            no_proxy=self._psrp_ignore_proxy,
            max_envelope_size=self._psrp_max_envelope_size,
            operation_timeout=self._psrp_operation_timeout,
            certificate_key_pem=self._psrp_certificate_key_pem,
            certificate_pem=self._psrp_certificate_pem,
            credssp_auth_mechanism=self._psrp_credssp_auth_mechanism,
            credssp_disable_tlsv1_2=self._psrp_credssp_disable_tlsv1_2,
            credssp_minimum_version=self._psrp_credssp_minimum_version,
            negotiate_send_cbt=self._psrp_negotiate_send_cbt,
            negotiate_delegate=self._psrp_negotiate_delegate,
            negotiate_hostname_override=self._psrp_negotiate_hostname_override,
            negotiate_service=self._psrp_negotiate_service,
        )

        # Check if PSRP version supports newer read_timeout argument (needs pypsrp 0.3.0+)
        if hasattr(pypsrp, 'FEATURES') and 'wsman_read_timeout' in pypsrp.FEATURES:
            self._psrp_conn_kwargs['read_timeout'] = self._psrp_read_timeout
        elif self._psrp_read_timeout is not None:
            display.warning("ansible_psrp_read_timeout is unsupported by the current psrp version installed, "
                            "using ansible_psrp_connection_timeout value for read_timeout instead.")

        # Check if PSRP version supports newer reconnection_retries argument (needs pypsrp 0.3.0+)
        if hasattr(pypsrp, 'FEATURES') and 'wsman_reconnections' in pypsrp.FEATURES:
            self._psrp_conn_kwargs['reconnection_retries'] = self._psrp_reconnection_retries
            self._psrp_conn_kwargs['reconnection_backoff'] = self._psrp_reconnection_backoff
        else:
            if self._psrp_reconnection_retries is not None:
                display.warning("ansible_psrp_reconnection_retries is unsupported by the current psrp version installed.")
            if self._psrp_reconnection_backoff is not None:
                display.warning("ansible_psrp_reconnection_backoff is unsupported by the current psrp version installed.")

        # add in the extra args that were set
        for arg in extra_args.intersection(supported_args):
            option = self.get_option('_extras')['ansible_psrp_%s' % arg]
            self._psrp_conn_kwargs[arg] = option

    def _exec_psrp_script(self, script, input_data=None, use_local_scope=True, arguments=None):
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

    def _parse_pipeline_result(self, pipeline):
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
            stderr_list.append(error_msg)

        if len(self.host.ui.stderr) > 0:
            stderr_list += self.host.ui.stderr
        stderr = u"\r\n".join([to_text(o) for o in stderr_list])

        display.vvvvv("PSRP RC: %d" % rc, host=self._psrp_host)
        display.vvvvv("PSRP STDOUT: %s" % stdout, host=self._psrp_host)
        display.vvvvv("PSRP STDERR: %s" % stderr, host=self._psrp_host)

        # reset the host back output back to defaults, needed if running
        # multiple pipelines on the same RunspacePool
        self.host.rc = 0
        self.host.ui.stdout = []
        self.host.ui.stderr = []

        return rc, to_bytes(stdout, encoding='utf-8'), to_bytes(stderr, encoding='utf-8')

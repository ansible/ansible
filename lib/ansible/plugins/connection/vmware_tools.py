# Copyright (c) 2018 Deric Crago <deric.crago@gmail.com>
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

import re
from os.path import dirname, exists, getsize
from socket import gaierror
from ssl import SSLEOFError, SSLError
from time import sleep

import requests
import urllib3

from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase
from ansible.utils.path import makedirs_safe

try:
    from pyVim.connect import Disconnect, SmartConnect, SmartConnectNoSSL
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError as e:
    HAS_PYVMOMI = False
    PYVMOMI_IMPORT_ERROR = e


__metaclass__ = type

DOCUMENTATION = """
    author: Deric Crago <deric.crago@gmail.com>
    connection: vmware_tools
    short_description: Execute modules via VMware Tools.
    description:
      - Execute modules via VMware Tools.
      - "Note: Windows VMs will need to have C(ansible_shell_type: powershell) set."
    version_added: "2.8"
    requirements:
      - pyvmomi (python library)
    options:
      connection_address:
        description:
          - Address for the connection (vCenter or ESXi Host).
        vars:
          - name: ansible_vmware_tools_connection_address
        required: True
      connection_username:
        description:
          - Username for the connection.
          - "Requires the following permissions on the VM:
               - VirtualMachine.GuestOperations.Execute
               - VirtualMachine.GuestOperations.Modify
               - VirtualMachine.GuestOperations.Query"
        vars:
          - name: ansible_vmware_tools_connection_username
        required: True
      connection_password:
        description:
          - Password for the connection.
        vars:
          - name: ansible_vmware_tools_connection_password
        required: True
      connection_verify_ssl:
        description:
          - Verify SSL for the connection.
          - "Note: This will verify SSL for both C(connection_address) and the ESXi host running the VM."
        vars:
          - name: ansible_vmware_tools_connection_verify_ssl
        default: True
        type: bool
      connection_ignore_ssl_warnings:
        description:
          - Ignore SSL warnings for the connection.
        vars:
          - name: ansible_vmware_tools_connection_ignore_ssl_warnings
        default: False
        type: bool
      vm_path:
        description:
          - VM path relative to the connection.
          - "vCenter Example: C(Datacenter/vm/Discovered virtual machine/testVM) (Needs to include C(vm) between the Datacenter and the rest of the VM path.)"
          - "ESXi Host Example: C(ha-datacenter/vm/testVM) (Needs to include C(vm) between the Datacenter (C(ha-datacenter)) and the rest of the VM path.)"
        vars:
          - name: ansible_vmware_tools_vm_path
        required: True
      vm_username:
        description:
          - VM username.
        vars:
          - name: ansible_vmware_tools_vm_username
        required: True
      vm_password:
        description:
          - VM password.
        vars:
          - name: ansible_vmware_tools_vm_password
        required: True
      exec_command_sleep_interval:
        description:
          - exec command sleep interval in seconds.
        vars:
          - name: ansible_vmware_tools_exec_command_sleep_interval
        default: 5
        type: integer
      file_chunk_size:
        description:
          - File chunk size.
          - "(Applicable when writing a file to disk, example: using the C(fetch) module.)"
        vars:
          - name: ansible_vmware_tools_file_chunk_size
        default: 128
        type: integer
"""


class Connection(ConnectionBase):
    """VMware Tools Connection."""

    transport = "vmware_tools"

    @property
    def connection_address(self):
        """Read-only property holding the connection address."""
        return self.get_option("connection_address")

    @property
    def connection_verify_ssl(self):
        """Read-only property holding whether the connection should verify ssl."""
        return self.get_option("connection_verify_ssl")

    @property
    def authManager(self):
        """Guest Authentication Manager."""
        return self._si.content.guestOperationsManager.authManager

    @property
    def fileManager(self):
        """Guest File Manager."""
        return self._si.content.guestOperationsManager.fileManager

    @property
    def processManager(self):
        """Guest Process Manager."""
        return self._si.content.guestOperationsManager.processManager

    @property
    def windowsGuest(self):
        """Return if VM guest family is windows."""
        return self.vm.guest.guestFamily == "windowsGuest"

    def __init__(self, *args, **kwargs):
        """init."""
        super(Connection, self).__init__(*args, **kwargs)
        if hasattr(self, "_shell") and self._shell.SHELL_FAMILY == "powershell":
            self.module_implementation_preferences = (".ps1", ".exe", "")
            self.become_methods = ["runas"]
            self.allow_executable = False
            self.has_pipelining = True
            self.allow_extras = True

    def _establish_connection(self):
        connection_kwargs = {"host": self.connection_address, "user": self.get_option("connection_username"), "pwd": self.get_option("connection_password")}

        if self.connection_verify_ssl:
            connect = SmartConnect
        else:
            if self.get_option("connection_ignore_ssl_warnings"):
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            connect = SmartConnectNoSSL

        try:
            self._si = connect(**connection_kwargs)
        except SSLError:
            raise AnsibleError("SSL Error: Certificate verification failed.")
        except (gaierror, SSLEOFError):
            raise AnsibleError("Connection Error: Unable to connect to '%s'." % to_native(connection_kwargs["host"]))
        except vim.fault.InvalidLogin as e:
            raise AnsibleError("Connection Login Error: %s" % to_native(e.msg))

    def _establish_vm(self):
        searchIndex = self._si.content.searchIndex
        self.vm = searchIndex.FindByInventoryPath(self.get_option("vm_path"))

        if self.vm is None:
            raise AnsibleError("Unable to find VM by path '%s'" % to_native(self.get_option("vm_path")))

        self.vm_auth = vim.NamePasswordAuthentication(
            username=self.get_option("vm_username"), password=self.get_option("vm_password"), interactiveSession=False
        )

        try:
            self.authManager.ValidateCredentialsInGuest(vm=self.vm, auth=self.vm_auth)
        except vim.fault.InvalidPowerState as e:
            raise AnsibleError("VM Power State Error: %s" % to_native(e.msg))
        except vim.fault.RestrictedVersion as e:
            raise AnsibleError("Restricted Version Error: %s" % to_native(e.msg))
        except vim.fault.GuestOperationsUnavailable as e:
            raise AnsibleError("VM Guest Operations (VMware Tools) Error: %s" % to_native(e.msg))
        except vim.fault.InvalidGuestLogin as e:
            raise AnsibleError("VM Login Error: %s" % to_native(e.msg))
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))

    def _connect(self):
        if not HAS_PYVMOMI:
            raise AnsibleError("missing 'pyvmomi' or dependencies: %s" % to_native(PYVMOMI_IMPORT_ERROR))

        super(Connection, self)._connect()

        if self.connected:
            pass

        self._establish_connection()
        self._establish_vm()

        self._connected = True

    def close(self):
        """Close connection."""
        super(Connection, self).close()

        Disconnect(self._si)
        self._connected = False

    def reset(self):
        """Reset the connection."""
        super(Connection, self).reset()

        self.close()
        self._connect()

    def create_temporary_file_in_guest(self, prefix="", suffix=""):
        """Create a temporary file in the VM."""
        try:
            return self.fileManager.CreateTemporaryFileInGuest(vm=self.vm, auth=self.vm_auth, prefix=prefix, suffix=suffix)
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))

    def _get_program_spec_program_path_and_arguments(self, cmd):
        if self.windowsGuest:
            cmd_parts = self._shell._encode_script(cmd, as_list=False, strict_mode=False, preserve_rc=False)

            program_path = "cmd.exe"
            arguments = "/c %s" % cmd_parts
        else:
            program_path = self._play_context.executable
            arguments = re.sub(r"^%s\s*" % program_path, "", cmd)

        return program_path, arguments

    def _get_guest_program_spec(self, cmd, stdout, stderr):
        guest_program_spec = vim.GuestProgramSpec()

        program_path, arguments = self._get_program_spec_program_path_and_arguments(cmd)

        arguments += " 1> %s 2> %s" % (stdout, stderr)

        guest_program_spec.programPath = program_path
        guest_program_spec.arguments = arguments

        return guest_program_spec

    def _get_pid_info(self, pid):
        try:
            processes = self.processManager.ListProcessesInGuest(vm=self.vm, auth=self.vm_auth, pids=[pid])
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))
        return processes[0]

    def _fix_url_for_hosts(self, url):
        """
        Fix url if connection is a host.

        The host part of the URL is returned as '*' if the hostname to be used is the name of the server to which the call was made. For example, if the call is
        made to esx-svr-1.domain1.com, and the file is available for download from http://esx-svr-1.domain1.com/guestFile?id=1&token=1234, the URL returned may
        be http://*/guestFile?id=1&token=1234. The client replaces the asterisk with the server name on which it invoked the call.

        https://code.vmware.com/apis/358/vsphere#/doc/vim.vm.guest.FileManager.FileTransferInformation.html
        """
        return url.replace("*", self.connection_address)

    def _fetch_file_from_vm(self, guestFilePath):
        try:
            fileTransferInformation = self.fileManager.InitiateFileTransferFromGuest(vm=self.vm, auth=self.vm_auth, guestFilePath=guestFilePath)
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))

        url = self._fix_url_for_hosts(fileTransferInformation.url)
        response = requests.get(url, verify=self.connection_verify_ssl, stream=True)

        if response.status_code != 200:
            raise AnsibleError("Failed to fetch file")

        return response

    def delete_file_in_guest(self, filePath):
        """Delete file from VM."""
        try:
            self.fileManager.DeleteFileInGuest(vm=self.vm, auth=self.vm_auth, filePath=filePath)
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """Execute command."""
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        stdout = self.create_temporary_file_in_guest(suffix=".stdout")
        stderr = self.create_temporary_file_in_guest(suffix=".stderr")

        guest_program_spec = self._get_guest_program_spec(cmd, stdout, stderr)

        try:
            pid = self.processManager.StartProgramInGuest(vm=self.vm, auth=self.vm_auth, spec=guest_program_spec)
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))
        except vim.fault.FileNotFound as e:
            raise AnsibleError("StartProgramInGuest Error: %s" % to_native(e.msg))

        pid_info = self._get_pid_info(pid)

        while pid_info.endTime is None:
            sleep(self.get_option("exec_command_sleep_interval"))
            pid_info = self._get_pid_info(pid)

        stdout_response = self._fetch_file_from_vm(stdout)
        self.delete_file_in_guest(stdout)

        stderr_response = self._fetch_file_from_vm(stderr)
        self.delete_file_in_guest(stderr)

        return pid_info.exitCode, stdout_response.text, stderr_response.text

    def fetch_file(self, in_path, out_path):
        """Fetch file."""
        super(Connection, self).fetch_file(in_path, out_path)

        makedirs_safe(dirname(out_path))

        in_path_response = self._fetch_file_from_vm(in_path)

        with open(out_path, "wb") as fd:
            for chunk in in_path_response.iter_content(chunk_size=self.get_option("file_chunk_size")):
                fd.write(chunk)

    def put_file(self, in_path, out_path):
        """Put file."""
        super(Connection, self).put_file(in_path, out_path)

        if not exists(to_bytes(in_path, errors="surrogate_or_strict")):
            raise AnsibleFileNotFound("file or module does not exist: '%s'" % to_native(in_path))

        try:
            put_url = self.fileManager.InitiateFileTransferToGuest(
                vm=self.vm, auth=self.vm_auth, guestFilePath=out_path, fileAttributes=vim.GuestFileAttributes(), fileSize=getsize(in_path), overwrite=True
            )
        except vim.fault.NoPermission as e:
            raise AnsibleError("No Permission Error: %s %s" % (to_native(e.msg), to_native(e.privilegeId)))

        url = self._fix_url_for_hosts(put_url)

        # file size of 'in_path' must be greater than 0
        with open(in_path, "rb") as fd:
            response = requests.put(url, verify=self.connection_verify_ssl, data=fd)

        if response.status_code != 200:
            raise AnsibleError("File transfer failed")

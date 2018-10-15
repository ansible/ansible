"""Docstring for public module."""
from __future__ import absolute_import, division, print_function

from pyVmomi import vim

from ansible.plugins.connection.vmware_tools import Connection as VMwareToolsConnection
from ansible.module_utils._text import to_native

__metaclass__ = type

DOCUMENTATION = """
    author: Deric Crago <deric.crago@gmail.com>
    connection: vmware_tools
    short_description: Execute modules via VMware Tools.
    description:
      - Execute modules via VMware Tools.
    version_added: "2.8"
    requirements:
      - pyvmomi (python library)
    options:
      connection_address:
        description:
          - Address for the connection
        vars:
          - name: ansible_vmware_tools_connection_address
        required: True
      connection_username:
        description:
          - Username for the connection
        vars:
          - name: ansible_vmware_tools_connection_username
        required: True
      connection_password:
        description:
          - Password for the connection
        vars:
          - name: ansible_vmware_tools_connection_password
        required: True
      connection_verify_ssl:
        description:
          - Verify SSL for the connection
        vars:
          - name: ansible_vmware_tools_connection_verify_ssl
        default: True
        type: bool
      connection_ignore_ssl_warnings:
        description:
          - Ignore SSL warnings for the connection
        vars:
          - name: ansible_vmware_tools_connection_ignore_ssl_warnings
        default: False
        type: bool
      vm_path:
        description:
          - VM path relative to vCenter.
          - Example: C(Datacenter/vm/Discovered virtual machine/testVM) (Needs to include C(vm) between the Datacenter and the rest of the VM path.)
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
        vars:
          - name: ansible_vmware_tools_file_chunk_size
        default: 128
        type: integer
"""


class Connection(VMwareToolsConnection):
    """VMware Tools Connection."""

    transport = "win_vmware_tools"
    module_implementation_preferences = (".ps1", ".exe", "")
    become_methods = ["runas"]
    allow_executable = False
    has_pipelining = True
    allow_extras = True

    @property
    def supported_guest_family(self):
        """Return if VM guest family is supported."""
        return self.vm.guest.guestFamily == "windowsGuest"

    def __init__(self, *args, **kwargs):
        """init."""
        self._shell_type = "powershell"
        super(Connection, self).__init__(*args, **kwargs)

    def _get_program_spec_program_path_and_arguments(self, cmd):
        cmd_parts = self._shell._encode_script(cmd, as_list=False, strict_mode=False, preserve_rc=False)

        program_path = "cmd.exe"
        arguments = "/c %s" % cmd_parts

        return program_path, arguments

    def guestFileAttributes(self):
        """Return GuestWindowsFileAttributes."""
        return vim.GuestWindowsFileAttributes()

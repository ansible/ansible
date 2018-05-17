#
# (c) 2017 Red Hat Inc.
#
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import ABCMeta, abstractmethod
from functools import wraps

from ansible.errors import AnsibleError
from ansible.module_utils.six import with_metaclass
from ansible.module_utils._text import to_bytes

try:
    from ncclient.operations import RPCError
    from ncclient.xml_ import to_xml, to_ele
except ImportError:
    raise AnsibleError("ncclient is not installed")


def ensure_connected(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self._connection._connected:
            self._connection._connect()
        return func(self, *args, **kwargs)
    return wrapped


class NetconfBase(with_metaclass(ABCMeta, object)):
    """
    A base class for implementing Netconf connections

    .. note:: Unlike most of Ansible, nearly all strings in
        :class:`TerminalBase` plugins are byte strings.  This is because of
        how close to the underlying platform these plugins operate.  Remember
        to mark literal strings as byte string (``b"string"``) and to use
        :func:`~ansible.module_utils._text.to_bytes` and
        :func:`~ansible.module_utils._text.to_text` to avoid unexpected
        problems.

        List of supported rpc's:
            :get: Retrieves running configuration and device state information
            :get_config: Retrieves the specified configuration from the device
            :edit_config: Loads the specified commands into the remote device
            :commit: Load configuration from candidate to running
            :discard_changes: Discard changes to candidate datastore
            :validate: Validate the contents of the specified configuration.
            :lock: Allows the client to lock the configuration system of a device.
            :unlock: Release a configuration lock, previously obtained with the lock operation.
            :copy_config: create or replace an entire configuration datastore with the contents of another complete
                          configuration datastore.
            :get-schema: Retrieves the required schema from the device
            :get_capabilities: Retrieves device information and supported rpc methods

            For JUNOS:
            :execute_rpc: RPC to be execute on remote device
            :load_configuration: Loads given configuration on device

        Note: rpc support depends on the capabilites of remote device.

        :returns: Returns output received from remote device as byte string
        Note: the 'result' or 'error' from response should to be converted to object
              of ElementTree using 'fromstring' to parse output as xml doc

              'get_capabilities()' returns 'result' as a json string.

            Usage:
            from ansible.module_utils.connection import Connection

            conn = Connection()
            data = conn.execute_rpc(rpc)
            reply = fromstring(reply)

            data = conn.get_capabilities()
            json.loads(data)

            conn.load_configuration(config=[''set system ntp server 1.1.1.1''], action='set', format='text')
    """

    def __init__(self, connection):
        self._connection = connection
        self.m = self._connection._manager

    @ensure_connected
    def rpc(self, name):
        """RPC to be execute on remote device
           :name: Name of rpc in string format"""
        try:
            obj = to_ele(name)
            resp = self.m.rpc(obj)
            return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
        except RPCError as exc:
            msg = exc.data_xml if hasattr(exc, 'data_xml') else exc.xml
            raise Exception(to_xml(msg))

    @ensure_connected
    def get_config(self, source=None, filter=None):
        """Retrieve all or part of a specified configuration
           (by default entire configuration is retrieved).

        :param source: Name of the configuration datastore being queried, defaults to running datastore
        :param filter: This argument specifies the portion of the configuration data to retrieve
        :return: Returns xml string containing the RPC response received from remote host
        """
        if isinstance(filter, list):
            filter = tuple(filter)

        if not source:
            source = 'running'
        resp = self.m.get_config(source=source, filter=filter)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def get(self, filter=None):
        """Retrieve device configuration and state information.

        :param filter: This argument specifies the portion of the state data to retrieve
                        (by default entire state data is retrieved)
        :return: Returns xml string containing the RPC response received from remote host
        """
        if isinstance(filter, list):
            filter = tuple(filter)
        resp = self.m.get(filter=filter)
        response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
        return response

    @ensure_connected
    def edit_config(self, *args, **kwargs):
        """Loads all or part of the specified *config* to the *target* configuration datastore.

            :target: is the name of the configuration datastore being edited
            :config: is the configuration, which must be rooted in the `config` element.
                        It can be specified either as a string or an :class:`~xml.etree.ElementTree.Element`.
            :default_operation: if specified must be one of { `"merge"`, `"replace"`, or `"none"` }
            :test_option: if specified must be one of { `"test_then_set"`, `"set"` }
            :error_option: if specified must be one of { `"stop-on-error"`, `"continue-on-error"`, `"rollback-on-error"` }
            The `"rollback-on-error"` *error_option* depends on the `:rollback-on-error` capability.
        """
        resp = self.m.edit_config(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def validate(self, *args, **kwargs):
        """Validate the contents of the specified configuration.
        :source: is the name of the configuration datastore being validated or `config`
        element containing the configuration subtree to be validated
        """
        resp = self.m.validate(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def copy_config(self, *args, **kwargs):
        """Create or replace an entire configuration datastore with the contents of another complete
        configuration datastore.
        :source: is the name of the configuration datastore to use as the source of the
                 copy operation or `config` element containing the configuration subtree to copy
        :target: is the name of the configuration datastore to use as the destination of the copy operation"""
        resp = self.m.copy_config(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def lock(self, target=None):
        """
        Allows the client to lock the configuration system of a device.
        :param target: is the name of the configuration datastore to lock,
                        defaults to candidate datastore
        :return: Returns xml string containing the RPC response received from remote host
        """
        if not target:
            target = 'candidate'
        resp = self.m.lock(target=target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def unlock(self, target=None):
        """
        Release a configuration lock, previously obtained with the lock operation.
        :param target: is the name of the configuration datastore to unlock,
                       defaults to candidate datastore
        :return: Returns xml string containing the RPC response received from remote host
        """
        """Release a configuration lock, previously obtained with the lock operation.
        :target: is the name of the configuration datastore to unlock
        """
        if not target:
            target = 'candidate'
        resp = self.m.unlock(target=target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def discard_changes(self):
        """
        Revert the candidate configuration to the currently running configuration.
        Any uncommitted changes are discarded.
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.discard_changes()
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def commit(self, *args, **kwargs):
        """Commit the candidate configuration as the device's new current configuration.
           Depends on the `:candidate` capability.
           A confirmed commit (i.e. if *confirmed* is `True`) is reverted if there is no
           followup commit within the *timeout* interval. If no timeout is specified the
           confirm timeout defaults to 600 seconds (10 minutes).
           A confirming commit may have the *confirmed* parameter but this is not required.
           Depends on the `:confirmed-commit` capability.
        :confirmed: whether this is a confirmed commit
        :timeout: specifies the confirm timeout in seconds
        """
        resp = self.m.commit(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def validate(self, *args, **kwargs):
        """Validate the contents of the specified configuration.
           :source: name of configuration data store"""
        resp = self.m.validate(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def get_schema(self, *args, **kwargs):
        """Retrieves the required schema from the device
        """
        resp = self.m.get_schema(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @ensure_connected
    def locked(self, *args, **kwargs):
        resp = self.m.locked(*args, **kwargs)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    @abstractmethod
    def get_capabilities(self):
        """Retrieves device information and supported
        rpc methods by device platform and return result
        as a string
        """
        pass

    @staticmethod
    def guess_network_os(obj):
        """Identifies the operating system of
            network device.
        """
        pass

    def get_base_rpc(self):
        """Returns list of base rpc method supported by remote device"""
        return ['get_config', 'edit_config', 'get_capabilities', 'get']

    def put_file(self, source, destination):
        """Copies file over scp to remote device"""
        pass

    def fetch_file(self, source, destination):
        """Fetch file over scp from remote device"""
        pass

    def get_device_operations(self, server_capabilities):
        operations = {}
        capabilities = '\n'.join(server_capabilities)
        operations['supports_commit'] = True if ':candidate' in capabilities else False
        operations['supports_defaults'] = True if ':with-defaults' in capabilities else False
        operations['supports_confirm_commit'] = True if ':confirmed-commit' in capabilities else False
        operations['supports_startup'] = True if ':startup' in capabilities else False
        operations['supports_xpath'] = True if ':xpath' in capabilities else False
        operations['supports_writeable_running'] = True if ':writable-running' in capabilities else False

        operations['lock_datastore'] = []
        if operations['supports_writeable_running']:
            operations['lock_datastore'].append('running')

        if operations['supports_commit']:
            operations['lock_datastore'].append('candidate')

        if operations['supports_startup']:
            operations['lock_datastore'].append('startup')

        operations['supports_lock'] = True if len(operations['lock_datastore']) else False

        return operations

# TODO Restore .xml, when ncclient supports it for all platforms

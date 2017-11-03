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

from ansible.module_utils.six import with_metaclass


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
            :get_config: Retrieves the specified configuration from the device
            :edit_config: Loads the specified commands into the remote device
            :get: Execute specified command on remote device
            :get_capabilities: Retrieves device information and supported rpc methods
            :commit: Load configuration from candidate to running
            :discard_changes: Discard changes to candidate datastore
            :validate: Validate the contents of the specified configuration.
            :lock: Allows the client to lock the configuration system of a device.
            :unlock: Release a configuration lock, previously obtained with the lock operation.
            :copy_config: create or replace an entire configuration datastore with the contents of another complete
                          configuration datastore.
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
    def get_config(self, *args, **kwargs):
        """Retrieve all or part of a specified configuration.
           :source: name of the configuration datastore being queried
           :filter: specifies the portion of the configuration to retrieve
           (by default entire configuration is retrieved)"""
        return self.m.get_config(*args, **kwargs).data_xml

    @ensure_connected
    def get(self, *args, **kwargs):
        """Retrieve running configuration and device state information.
        *filter* specifies the portion of the configuration to retrieve
        (by default entire configuration is retrieved)
        """
        return self.m.get(*args, **kwargs).data_xml

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
        return self.m.get_config(*args, **kwargs).data_xml

    @ensure_connected
    def validate(self, *args, **kwargs):
        """Validate the contents of the specified configuration.
        :source: is the name of the configuration datastore being validated or `config`
        element containing the configuration subtree to be validated
        """
        return self.m.validate(*args, **kwargs).data_xml

    @ensure_connected
    def copy_config(self, *args, **kwargs):
        """Create or replace an entire configuration datastore with the contents of another complete
        configuration datastore.
        :source: is the name of the configuration datastore to use as the source of the
                 copy operation or `config` element containing the configuration subtree to copy
        :target: is the name of the configuration datastore to use as the destination of the copy operation"""
        return self.m.copy_config(*args, **kwargs).data_xml

    @ensure_connected
    def lock(self, *args, **kwargs):
        """Allows the client to lock the configuration system of a device.
        *target* is the name of the configuration datastore to lock
        """
        return self.m.lock(*args, **kwargs).data_xml

    @ensure_connected
    def unlock(self, *args, **kwargs):
        """Release a configuration lock, previously obtained with the lock operation.
        :target: is the name of the configuration datastore to unlock
        """
        return self.m.lock(*args, **kwargs).data_xml

    @ensure_connected
    def discard_changes(self, *args, **kwargs):
        """Revert the candidate configuration to the currently running configuration.
        Any uncommitted changes are discarded."""
        return self.m.discard_changes(*args, **kwargs).data_xml

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
        return self.m.commit(*args, **kwargs).data_xml

    @abstractmethod
    def get_capabilities(self, commands):
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

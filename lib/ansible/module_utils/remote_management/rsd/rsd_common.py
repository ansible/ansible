# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Igor D.C. - <igor.duarte.cardoso@intel.com>
#   - Marco Chiappero - <marco.chiappero@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import (env_fallback, missing_required_lib,
                                        AnsibleModule)
import traceback

try:
    from cachetools import cached, LRUCache
    HAS_CACHETOOLS = True
    CACHETOOLS_IMP_ERR = None
except ImportError:
    HAS_CACHETOOLS = False
    CACHETOOLS_IMP_ERR = traceback.format_exc()

try:
    import rsd_lib
    import sushy
    HAS_RSDLIB = True
    RSDLIB_IMP_ERR = None
except ImportError:
    HAS_RSDLIB = False
    RSDLIB_IMP_ERR = traceback.format_exc()


def unchanged(func):
    return func


# Prevent NameError if cachetools are not installed
cache = cached(cache=LRUCache(maxsize=1024)) if HAS_CACHETOOLS else unchanged


class RSD(object):

    class PodmInfo(object):

        def __init__(self):
            self._host = None
            self._port = 8443
            self._protocol = 'http'
            self._verify_cert = False

        @property
        def host(self):
            return self._host

        @host.setter
        def host(self, value):
            if value and isinstance(value, str):
                self._host = value
            else:
                raise ValueError("Invalid hostname")

        @property
        def port(self):
            return self._port

        @port.setter
        def port(self, value):
            if 1 < value and value <= 65535:
                self._port = value
            else:
                raise ValueError("Invalid port number")

        @property
        def protocol(self):
            return self._protocol

        @protocol.setter
        def protocol(self, value):
            if value.lower() in ['https', 'http']:
                self._protocol = value
            else:
                raise ValueError("Must be a http or https")

        @property
        def verify_cert(self):
            return self._verify_cert

        @verify_cert.setter
        def verify_cert(self, value):
            self._verify_cert = value

        def is_valid(self):
            if self._host and self._port:
                return True

            return False

        def to_url(self):
            endpoint = "/redfish/v1"  # might be influenced by <version>

            return "{0}://{1}:{2}{3}".format(
                self._protocol, self._host, self._port, endpoint)

    class AuthInfo():

        def __init__(self):
            self.username = None
            self.password = None

    RSD_BACKEND_ARGS = dict(
        id=dict(
            type='dict',
            required=True,
            options=dict(
                type=dict(
                    type='str',
                    required=False,
                    choices=['name', 'identity', 'uuid'],
                    default='identity'
                ),
                value=dict(
                    type='str',
                    required=True
                )
            )
        ),
        podm=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                host=dict(
                    type='str',
                    fallback=(env_fallback, ['PODM_HOST']),
                    required=True,
                    aliases=['hostname']
                ),
                port=dict(
                    type='int',
                    fallback=(env_fallback, ['PODM_PORT']),
                    default=8443,
                ),
                protocol=dict(
                    type='str',
                    default='https',
                    choices=['https', 'http']
                ),
                validate_cert=dict(
                    type='bool',
                    default=False,
                    aliases=['verify_cert']
                ),
            ),
        ),
        auth=dict(
            type='dict',
            apply_defaults=True,
            options=dict(
                username=dict(
                    type='str',
                    fallback=(env_fallback, ['PODM_USERNAME']),
                    required=True,
                    no_log=True,
                    aliases=['user']
                ),
                password=dict(
                    type='str',
                    fallback=(env_fallback, ['PODM_PASSWORD']),
                    required=True,
                    no_log=True,
                    aliases=['pass']
                ),
            ),
        )
    )

    def __init__(self, argument_spec, bypass_checks=False, no_log=False,
                 check_invalid_arguments=None, mutually_exclusive=None,
                 required_together=None, required_one_of=None,
                 add_file_common_args=False, supports_check_mode=False,
                 required_if=None):

        full_arg_spec = dict()
        full_arg_spec.update(RSD.RSD_BACKEND_ARGS)  # args spec to this class
        full_arg_spec.update(argument_spec)   # args from derived class

        self.module = AnsibleModule(
            argument_spec=full_arg_spec,
            supports_check_mode=supports_check_mode,
            bypass_checks=bypass_checks,
            no_log=no_log,
            add_file_common_args=add_file_common_args,
            check_invalid_arguments=check_invalid_arguments,
            mutually_exclusive=mutually_exclusive,
            required_together=required_together,
            required_if=required_if,
            required_one_of=required_one_of
        )

        if not HAS_RSDLIB:
            self.module.fail_json(
                msg=missing_required_lib('rsd-lib',
                                         url='https://opendev.org/x/rsd-lib'),
                exception=RSDLIB_IMP_ERR)

        if not HAS_CACHETOOLS:
            self.module.fail_json(msg=missing_required_lib('cachetools'),
                                  exception=CACHETOOLS_IMP_ERR)

        podm, credentials = self._parse_connection_info()
        self._connect(podm, credentials)

        self.module.debug("rsd-lib setup completed")

    def _parse_connection_info(self):
        endpoint = RSD.PodmInfo()
        podm_info = self.module.params['podm']
        endpoint.host = podm_info['host']
        endpoint.port = podm_info['port']
        endpoint.protocol = podm_info['protocol']
        endpoint.verify_cert = podm_info['validate_cert']

        if not endpoint.is_valid():
            self.module.fail_json(msg='Invalid PODM info')

        credentials = RSD.AuthInfo()
        auth_info = self.module.params['auth']
        credentials.username = auth_info['username']
        credentials.password = auth_info['password']

        if not credentials.username or not credentials.password:
            self.module.fail_json(msg='Missing endpoint credentials')

        return endpoint, credentials

    def _connect(self, podm_info, auth_info):
        try:
            self.rsd = rsd_lib.RSDLib(
                base_url=podm_info.to_url(),
                verify=podm_info.verify_cert,
                username=auth_info.username,
                password=auth_info.password
            ).factory()
        except (sushy.exceptions.ResourceNotFoundError,
                sushy.exceptions.ConnectionError,
                sushy.exceptions.HTTPError) as e:
            self.module.fail_json(
                msg="Failed to setup and endpoint connection: {0}".format(
                    str(e)))

        self.module.debug("Connection with PODM established")

    def _get_nodes_collection(self):
        return self.rsd.get_node_collection().get_members()

    def _get_node(self):
        params = self.module.params
        type = params['id']['type']
        value = params['id']['value']

        if type == 'identity':
            node_uri = "v1/Nodes/" + str(value)
            try:
                return self.rsd.get_node(node_uri)
            except sushy.exceptions.ResourceNotFoundError:
                self.module.fail_json(
                    msg="There is no node with such ID: {0}".format(value))
        else:
            nodes = self._get_nodes_collection()

            if type == 'name':
                node_match = [n for n in nodes if n.name == value]

                if len(node_match) == 1:
                    return node_match[0]
                elif len(node_match) > 1:
                    self.module.fail_json(msg="Multiple nodes found with "
                                          "given name: {0}".format(value))

            elif type == 'uuid':
                for n in nodes:
                    if n.uuid == value:
                        return n

            # not found
            self.module.fail_json(msg="There is no node with id type '{0}' "
                                  "and value: '{1}'".format(type, value))

    @staticmethod
    def _get_service_uri(res_uri):
        return "/".join(res_uri.split("/", 5)[:5])

    @cache
    def _get_storage_serv(self, stor_serv_resource_uri):
        stor_serv_uri = RSD._get_service_uri(stor_serv_resource_uri)
        return self.rsd.get_storage_service(stor_serv_uri)

    @cache
    def _get_fabric_serv(self, fabric_resource_uri):
        fab_uri = RSD._get_service_uri(fabric_resource_uri)
        return self.rsd.get_fabric(fab_uri)

    @cache
    def _get_system(self, sys_resource_uri):
        sys_uri = RSD._get_service_uri(sys_resource_uri)
        return self.rsd.get_system(sys_uri)

    def _get_volume(self, vol_uri):
        storage_serv = self._get_storage_serv(vol_uri)
        return storage_serv.volumes.get_member(vol_uri)

    def _get_drive(self, drive_uri):
        storage_serv = self._get_storage_serv(drive_uri)
        return storage_serv.drives.get_member(drive_uri)

    def _get_endpoint(self, endpt_uri):
        fabric = self._get_fabric_serv(endpt_uri)
        endpoint_col = fabric.endpoints
        return endpoint_col.get_member(endpt_uri)

    def _get_processor(self, proc_uri):
        system = self._get_system(proc_uri)
        return system.processors.get_member(proc_uri)

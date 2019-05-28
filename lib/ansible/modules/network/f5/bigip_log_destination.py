#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_log_destination
short_description: Manages log destinations on a BIG-IP.
description:
  - Manages log destinations on a BIG-IP.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the log destination.
    type: str
    required: True
  type:
    description:
      - Specifies the type of log destination.
      - Once created, this parameter cannot be changed.
    type: str
    choices:
      - remote-high-speed-log
      - remote-syslog
      - arcsight
      - splunk
      - management-port
      - ipfix
    required: True
  description:
    description:
      - The description of the log destination.
    type: str
  pool_settings:
    description:
      - This parameter is only available when C(type) is C(remote-high-speed-log).
      - Deprecated. Use the equivalent top-level parameters instead.
    suboptions:
      pool:
        description:
          - Specifies the existing pool of remote high-speed log servers where logs will be sent.
          - When creating a new destination (and C(type) is C(remote-high-speed-log)), this parameter
            is required.
        type: str
      protocol:
        description:
          - Specifies the protocol for the system to use to send logs to the pool of remote high-speed
            log servers, where the logs are stored.
          - When creating a new log destination (and C(type) is C(remote-high-speed-log)), if this
            parameter is not specified, the default is C(tcp).
        type: str
        choices:
          - tcp
          - udp
      distribution:
        description:
          - Specifies the distribution method used by the Remote High Speed Log destination to send
            messages to pool members.
          - When C(adaptive), connections to pool members will be added as required to provide enough
            logging bandwidth. This can have the undesirable effect of logs accumulating on only one
            pool member when it provides sufficient logging bandwidth on its own.
          - When C(balanced), sends each successive log to a new pool member, balancing the logs among
            them according to the pool's load balancing method.
          - When C(replicated), replicates each log to all pool members, for redundancy.
          - When creating a new log destination (and C(type) is C(remote-high-speed-log)), if this
            parameter is not specified, the default is C(adaptive).
        type: str
        choices:
          - adaptive
          - balanced
          - replicated
    type: dict
  syslog_settings:
    description:
      - This parameter is only available when C(type) is C(remote-syslog).
      - Deprecated. Use the equivalent top-level parameters instead.
    suboptions:
      syslog_format:
        description:
          - Specifies the method to use to format the logs associated with the remote Syslog log destination.
          - When creating a new log destination (and C(type) is C(remote-syslog)), if this parameter is
            not specified, the default is C(bsd-syslog).
          - The C(syslog) and C(rfc5424) choices are two ways of saying the same thing.
          - The C(bsd-syslog) and C(rfc3164) choices are two ways of saying the same thing.
        type: str
        choices:
          - bsd-syslog
          - syslog
          - legacy-bigip
          - rfc5424
          - rfc3164
      forward_to:
        description:
          - Specifies the management port log destination, which will be used to forward the logs to a
            single log server, or a remote high-speed log destination, which will be used to forward the
            logs to a pool of remote log servers.
          - When creating a new log destination (and C(type) is C(remote-syslog)), this parameter is required.
        type: str
    type: dict
  syslog_format:
    description:
      - Specifies the method to use to format the logs associated with the remote Syslog log destination.
      - When creating a new log destination (and C(type) is C(remote-syslog)), if this parameter is
        not specified, the default is C(bsd-syslog).
      - The C(syslog) and C(rfc5424) choices are two ways of saying the same thing.
      - The C(bsd-syslog) and C(rfc3164) choices are two ways of saying the same thing.
    type: str
    choices:
      - bsd-syslog
      - syslog
      - legacy-bigip
      - rfc5424
      - rfc3164
    version_added: 2.8
  forward_to:
    description:
      - When C(type) is C(remote-syslog), specifies the management port log destination, which will
        be used to forward the logs to a single log server, or a remote high-speed log destination,
        which will be used to forward the logs to a pool of remote log servers.
      - When C(type) is C(splunk) or C(arcsight), specifies the log destination to which logs are
        forwarded. This log destination may be a management port destination, a remote high-speed
        log destination, or a remote Syslog destination which is configured to send logs to an
        ArcSight or Splunk server.
      - When creating a new log destination and C(type) is C(remote-syslog), C(splunk), or C(arcsight),
        this parameter is required.
    type: str
    version_added: 2.8
  pool:
    description:
      - When C(type) is C(remote-high-speed-log), specifies the existing pool of remote high-speed
        log servers where logs will be sent.
      - When C(type) is C(ipfix), specifies the existing LTM pool of remote IPFIX collectors. Any
        BIG-IP application that uses this log destination sends its IP-traffic logs to this pool
        of collectors.
      - When creating a new destination and C(type) is C(remote-high-speed-log) or C(ipfix), this
        parameter is required.
    type: str
    version_added: 2.8
  protocol:
    description:
      - When C(type) is C(remote-high-speed-log), specifies the protocol for the system to use to
        send logs to the pool of remote high-speed log servers, where the logs are stored.
      - When C(type) is C(ipfix), can be IPFIX or Netflow v9, depending on the type of collectors
        you have in the pool that you specify.
      - When C(type) is C(management-port), specifies the protocol used to send messages to the
        specified location.
      - When C(type) is C(management-port), only C(tcp) and C(udp) are valid values.
    type: str
    choices:
      - tcp
      - udp
      - ipfix
      - netflow-9
    version_added: 2.8
  distribution:
    description:
      - Specifies the distribution method used by the Remote High Speed Log destination to send
        messages to pool members.
      - When C(adaptive), connections to pool members will be added as required to provide enough
        logging bandwidth. This can have the undesirable effect of logs accumulating on only one
        pool member when it provides sufficient logging bandwidth on its own.
      - When C(balanced), sends each successive log to a new pool member, balancing the logs among
        them according to the pool's load balancing method.
      - When C(replicated), replicates each log to all pool members, for redundancy.
      - When creating a new log destination and C(type) is C(remote-high-speed-log), if this
        parameter is not specified, the default is C(adaptive).
    type: str
    choices:
      - adaptive
      - balanced
      - replicated
    version_added: 2.8
  address:
    description:
      - Specifies the IP address that will receive messages from the specified local Log Destination.
      - This parameter is only available when C(type) is C(management-port).
      - When creating a new log destination and C(type) is C(management-port), this parameter
        is required.
    type: str
    version_added: 2.8
  port:
    description:
      - Specifies the port of the IP address that will receive messages from the specified local
        Log Destination.
      - This parameter is only available when C(type) is C(management-port).
      - When creating a new log destination and C(type) is C(management-port), this parameter
        is required.
    type: int
    version_added: 2.8
  transport_profile:
    description:
      - Is a transport profile based on either TCP or UDP.
      - This profile defines the TCP or UDP options used to send IP-traffic logs
        to the pool of collectors.
      - This parameter is only available when C(type) is C(ipfix).
    type: str
    version_added: 2.8
  server_ssl_profile:
    description:
      - If the C(transport_profile) is a TCP profile, you can use this field to
        choose a Secure Socket Layer (SSL) profile for sending logs to the IPFIX
        collectors.
      - An SSL server profile defines how to communicate securely over SSL or
        Transport Layer Security (TLS).
      - This parameter is only available when C(type) is C(ipfix).
    type: str
    version_added: 2.8
  template_retransmit_interval:
    description:
      - Enter the time (in seconds) between each transmission of IPFIX templates
        to the pool of IPFIX collectors.
      - The logging destination periodically retransmits all of its IPFIX templates
        at the interval you set in this field. These retransmissions are helpful
        for UDP, a lossy transport mechanism.
      - This parameter is only available when C(type) is C(ipfix).
    type: int
    version_added: 2.8
  template_delete_delay:
    description:
      - Enter the time (in seconds) that the BIG-IP device should pause between
        deleting an obsolete IPFIX template and reusing its template ID.
      - This feature is useful for systems where you use iRules to create
        customized IPFIX templates.
    type: int
    version_added: 2.8
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a high-speed logging destination
  bigip_log_destination:
    name: foo
    type: remote-high-speed-log
    pool: my-ltm-pool
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a remote-syslog logging destination
  bigip_log_destination:
    name: foo
    type: remote-syslog
    syslog_format: rfc5424
    forward_to: my-destination
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
forward_to:
  description: The new Forward To value.
  returned: changed
  type: str
  sample: /Common/dest1
pool:
  description: The new Pool value.
  returned: changed
  type: str
  sample: /Common/pool1
distribution:
  description: The new Distribution Method value.
  returned: changed
  type: str
  sample: balanced
protocol:
  description: The new Protocol value.
  returned: changed
  type: str
  sample: tcp
syslog_format:
  description: The new Syslog format value.
  returned: changed
  type: str
  sample: syslog
address:
  description: The new Address value.
  returned: changed
  type: str
  sample: 1.2.3.2
port:
  description: The new Port value.
  returned: changed
  type: int
  sample: 2020
template_delete_delay:
  description: The new Template Delete Delay value.
  returned: changed
  type: int
  sample: 20
template_retransmit_interval:
  description: The new Template Retransmit Interval value.
  returned: changed
  type: int
  sample: 200
transport_profile:
  description: The new Transport Profile value.
  returned: changed
  type: str
  sample: /Common/tcp
server_ssl_profile:
  description: The new Server SSL Profile value.
  returned: changed
  type: str
  sample: /Common/serverssl
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class V1Parameters(AnsibleF5Parameters):
    """Base Parameters for remote-syslog

    """
    api_map = {
        'remoteHighSpeedLog': 'forward_to',
        'format': 'syslog_format'
    }

    api_attributes = [
        'remoteHighSpeedLog',
        'format'
    ]

    returnables = [
        'forward_to',
        'syslog_format'
    ]

    updatables = [
        'forward_to',
        'syslog_format',
        'type'
    ]


# TODO(Remove in 2.12)
class V1ModuleParameters(V1Parameters):
    @property
    def forward_to(self):
        if self._values['forward_to']:
            result = self._values['forward_to']
        else:
            if self._values['syslog_settings'] is None:
                return None
            result = self._values['syslog_settings'].get('forward_to', None)

        if result:
            result = fq_name(self.partition, result)
        return result

    @property
    def syslog_format(self):
        if self._values['syslog_format']:
            result = self._values['syslog_format']
        else:
            if self._values['syslog_settings'] is None:
                return None
            result = self._values['syslog_settings'].get('syslog_format', None)

        if result == 'syslog':
            result = 'rfc5424'
        if result == 'bsd-syslog':
            result = 'rfc3164'
        return result


# TODO(Remove in 2.12)
class V1ApiParameters(V1Parameters):
    @property
    def type(self):
        return 'remote-syslog'


# TODO(Remove in 2.12)
class V1Changes(V1Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


# TODO(Remove in 2.12)
class V1UsableChanges(V1Changes):
    pass


# TODO(Remove in 2.12)
class V1ReportableChanges(V1Changes):
    pass


# TODO(Remove in 2.12)
class V2Parameters(AnsibleF5Parameters):
    """Base Parameters for remote-high-speed-log

    """
    api_map = {
        'poolName': 'pool'
    }

    api_attributes = [
        'distribution',
        'poolName',
        'protocol'
    ]

    returnables = [
        'pool',
        'distribution',
        'protocol'
    ]

    updatables = [
        'pool',
        'distribution',
        'protocol',
        'type'
    ]


# TODO(Remove in 2.12)
class V2ModuleParameters(V2Parameters):
    @property
    def pool(self):
        if self._values['pool']:
            result = self._values['pool']
        else:
            if self._values['pool_settings'] is None:
                return None
            result = self._values['pool_settings'].get('pool', None)
        if result:
            result = fq_name(self.partition, result)
        return result

    @property
    def protocol(self):
        if self._values['protocol']:
            return self._values['protocol']
        else:
            if self._values['pool_settings'] is None:
                return None
            return self._values['pool_settings'].get('protocol', None)

    @property
    def distribution(self):
        if self._values['distribution']:
            return self._values['distribution']
        else:
            if self._values['pool_settings'] is None:
                return None
            return self._values['pool_settings'].get('distribution', None)


# TODO(Remove in 2.12)
class V2ApiParameters(V2Parameters):
    @property
    def type(self):
        return 'remote-high-speed-log'


# TODO(Remove in 2.12)
class V2Changes(V2Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


# TODO(Remove in 2.12)
class V2UsableChanges(V2Changes):
    pass


# TODO(Remove in 2.12)
class V2ReportableChanges(V2Changes):
    pass


class V3Parameters(AnsibleF5Parameters):
    api_map = {
        'forwardTo': 'forward_to',
        'poolName': 'pool',
        'remoteHighSpeedLog': 'forward_to',
        'format': 'syslog_format',
        'ipAddress': 'address',
        'protocolVersion': 'protocol',
        'templateDeleteDelay': 'template_delete_delay',
        'templateRetransmitInterval': 'template_retransmit_interval',
        'transportProfile': 'transport_profile',
        'serversslProfile': 'server_ssl_profile',
    }

    api_attributes = [
        'forwardTo',
        'distribution',
        'poolName',
        'protocol',
        'remoteHighSpeedLog',
        'format',
        'ipAddress',
        'port',
        'serversslProfile',
        'transportProfile',
        'templateRetransmitInterval',
        'templateDeleteDelay',
        'protocolVersion',
    ]

    returnables = [
        'forward_to',
        'pool',
        'distribution',
        'protocol',
        'syslog_format',
        'address',
        'port',
        'template_delete_delay',
        'template_retransmit_interval',
        'transport_profile',
        'server_ssl_profile',
    ]

    updatables = [
        'forward_to',
        'type',
        'pool',
        'distribution',
        'protocol',
        'syslog_format',
        'address',
        'port',
        'template_delete_delay',
        'template_retransmit_interval',
        'transport_profile',
        'server_ssl_profile',
        'type',
    ]


class V3ModuleParameters(V3Parameters):
    @property
    def forward_to(self):
        if self._values['forward_to'] is None:
            return None
        return fq_name(self.partition, self._values['forward_to'])

    @property
    def pool(self):
        if self._values['pool'] is None:
            return None
        return fq_name(self.partition, self._values['pool'])

    @property
    def syslog_format(self):
        if self._values['syslog_format'] is None:
            return None
        result = self._values['syslog_format']
        if result == 'syslog':
            result = 'rfc5424'
        if result == 'bsd-syslog':
            result = 'rfc3164'
        return result

    @property
    def server_ssl_profile(self):
        if self._values['server_ssl_profile'] is None:
            return None
        elif self._values['server_ssl_profile'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['server_ssl_profile'])

    @property
    def transport_profile(self):
        if self._values['transport_profile'] is None:
            return None
        return fq_name(self.partition, self._values['transport_profile'])


class V3ApiParameters(V3Parameters):
    pass


class V3Changes(V3Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class V3UsableChanges(V3Changes):
    pass


class V3ReportableChanges(V3Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def type(self):
        if self.want.type != self.have.type:
            raise F5ModuleError(
                "'type' cannot be changed once it is set."
            )

    @property
    def server_ssl_profile(self):
        return cmp_str_with_none(self.want.server_ssl_profile, self.have.server_ssl_profile)

    @property
    def transport_profile(self):
        return cmp_str_with_none(self.want.transport_profile, self.have.transport_profile)


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)

    def _set_changed_options(self):
        changed = {}
        for key in self.get_returnables():
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = self.get_usable_changes(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = self.get_updatables()
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = self.get_usable_changes(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = self.get_reportable_changes(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _validate_creation_parameters(self):
        pass

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._validate_creation_parameters()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False


class V1Manager(BaseManager):
    """Manages remote-syslog settings

    """

    def __init__(self, *args, **kwargs):
        super(V1Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def _validate_creation_parameters(self):
        if self.want.syslog_format is None:
            self.want.update({'syslog_format': 'bsd-syslog'})
        if self.want.forward_to is None:
            raise F5ModuleError(
                "'forward_to' is required when creating a new remote-syslog destination."
            )

    # TODO(In 2.12, these get_* methods should no longer be needed)
    def get_reportable_changes(self, params=None):
        if params:
            return V1ReportableChanges(params=params)
        return V1ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V1UsableChanges(params=params)
        return V1UsableChanges()

    def get_returnables(self):
        return V1ApiParameters.returnables

    def get_updatables(self):
        return V1ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V1ModuleParameters(params=params)
        return V1ModuleParameters()

    def get_api_params(self, params=None):
        if params:
            return V1ApiParameters(params=params)
        return V1ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-syslog/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-syslog/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-syslog/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-syslog/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-syslog/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'remote-syslog'
        return V1ApiParameters(params=response)


class V2Manager(BaseManager):
    """Manages remote-high-speed-log settings

    """
    def __init__(self, *args, **kwargs):
        super(V2Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_reportable_changes(self, params=None):
        if params:
            return V2ReportableChanges(params=params)
        return V2ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V2UsableChanges(params=params)
        return V2UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.protocol is None:
            self.want.update({'protocol': 'tcp'})
        if self.want.distribution is None:
            self.want.update({'distribution': 'adaptive'})
        if self.want.pool is None:
            raise F5ModuleError(
                "'pool' is required when creating a new remote-high-speed-log destination."
            )

    def get_returnables(self):
        return V2ApiParameters.returnables

    def get_updatables(self):
        return V2ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V2ModuleParameters(params=params)
        return V2ModuleParameters()

    def get_api_params(self, params=None):
        if params:
            return V2ApiParameters(params=params)
        return V2ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-high-speed-log/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-high-speed-log/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-high-speed-log/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-high-speed-log/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/remote-high-speed-log/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'remote-high-speed-log'
        return V2ApiParameters(params=response)


class V3Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(V3Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_reportable_changes(self, params=None):
        if params:
            return V3ReportableChanges(params=params)
        return V3ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V3UsableChanges(params=params)
        return V3UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.forward_to is None:
            raise F5ModuleError(
                "'forward_to' is required when creating a new arcsight destination."
            )

    def get_returnables(self):
        return V3ApiParameters.returnables

    def get_updatables(self):
        return V3ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V3ModuleParameters(params=params)
        return V3ModuleParameters()

    def get_api_params(self, params=None):
        if params:

            return V3ApiParameters(params=params)
        return V3ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/arcsight/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/arcsight/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/arcsight/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/arcsight/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/arcsight/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'arcsight'
        return V3ApiParameters(params=response)


class V4Manager(BaseManager):
    """Manager for Splunk

    Do not worry about the usage of V3 classes in this V4 manager.
    In Ansible 2.12, the Parameter classes will undergo a rename
    because of parameters being deprecated.

    The correct Parameter classes to use in this class are the
    V3 Parameter classes.

    """
    def __init__(self, *args, **kwargs):
        super(V4Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_reportable_changes(self, params=None):
        if params:
            return V3ReportableChanges(params=params)
        return V3ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V3UsableChanges(params=params)
        return V3UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.forward_to is None:
            raise F5ModuleError(
                "'forward_to' is required when creating a new splunk destination."
            )

    def get_returnables(self):
        return V3ApiParameters.returnables

    def get_updatables(self):
        return V3ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V3ModuleParameters(params=params)
        return V3ModuleParameters()

    def get_api_params(self, params=None):
        if params:

            return V3ApiParameters(params=params)
        return V3ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/splunk/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/splunk/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/splunk/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/splunk/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/splunk/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'splunk'
        return V3ApiParameters(params=response)


class V5Manager(BaseManager):
    """Manager for Management Port

    Do not worry about the usage of V3 classes in this V5 manager.
    In Ansible 2.12, the Parameter classes will undergo a rename
    because of parameters being deprecated.

    The correct Parameter classes to use in this class are the
    V3 Parameter classes.

    """
    def __init__(self, *args, **kwargs):
        super(V5Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_reportable_changes(self, params=None):
        if params:
            return V3ReportableChanges(params=params)
        return V3ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V3UsableChanges(params=params)
        return V3UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.address is None:
            raise F5ModuleError(
                "'address' is required when creating a new management-port destination."
            )
        if self.want.port is None:
            raise F5ModuleError(
                "'port' is required when creating a new management-port destination."
            )

    def get_returnables(self):
        return V3ApiParameters.returnables

    def get_updatables(self):
        return V3ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V3ModuleParameters(params=params)
        return V3ModuleParameters()

    def get_api_params(self, params=None):
        if params:

            return V3ApiParameters(params=params)
        return V3ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/management-port/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/management-port/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/management-port/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/management-port/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/management-port/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'management-port'
        return V3ApiParameters(params=response)


class V6Manager(BaseManager):
    """Manager for IPFIX

    Do not worry about the usage of V3 classes in this V6 manager.
    In Ansible 2.12, the Parameter classes will undergo a rename
    because of parameters being deprecated.

    The correct Parameter classes to use in this class are the
    V3 Parameter classes.

    """
    def __init__(self, *args, **kwargs):
        super(V6Manager, self).__init__(*args, **kwargs)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_reportable_changes(self, params=None):
        if params:
            return V3ReportableChanges(params=params)
        return V3ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V3UsableChanges(params=params)
        return V3UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.protocol is None:
            raise F5ModuleError(
                "'protocol' is required when creating a new ipfix destination."
            )
        if self.want.pool is None:
            raise F5ModuleError(
                "'port' is required when creating a new ipfix destination."
            )
        if self.want.transport_profile is None:
            raise F5ModuleError(
                "'transport_profile' is required when creating a new ipfix destination."
            )

    def get_returnables(self):
        return V3ApiParameters.returnables

    def get_updatables(self):
        return V3ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V3ModuleParameters(params=params)
        return V3ModuleParameters()

    def get_api_params(self, params=None):
        if params:

            return V3ApiParameters(params=params)
        return V3ApiParameters()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/ipfix/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/ipfix/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/ipfix/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/ipfix/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/log-config/destination/ipfix/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        response['type'] = 'ipfix'
        return V3ApiParameters(params=response)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.module = kwargs.get('module', None)

    def exec_module(self):
        if self.module.params['type'] == 'remote-syslog':
            manager = self.get_manager('v1')
        elif self.module.params['type'] == 'remote-high-speed-log':
            manager = self.get_manager('v2')
        elif self.module.params['type'] == 'arcsight':
            manager = self.get_manager('v3')
        elif self.module.params['type'] == 'splunk':
            manager = self.get_manager('v4')
        elif self.module.params['type'] == 'management-port':
            manager = self.get_manager('v5')
        elif self.module.params['type'] == 'ipfix':
            manager = self.get_manager('v6')
        else:
            raise F5ModuleError(
                "Unknown type specified."
            )
        result = manager.exec_module()
        return result

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)
        elif type == 'v3':
            return V3Manager(**self.kwargs)
        elif type == 'v4':
            return V4Manager(**self.kwargs)
        elif type == 'v5':
            return V5Manager(**self.kwargs)
        elif type == 'v6':
            return V6Manager(**self.kwargs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            type=dict(
                required=True,
                choices=[
                    'arcsight',
                    'remote-high-speed-log',
                    'remote-syslog',
                    'splunk',
                    'management-port',
                    'ipfix',
                ]
            ),
            description=dict(),
            syslog_format=dict(
                choices=[
                    'bsd-syslog',
                    'syslog',
                    'legacy-bigip',
                    'rfc5424',
                    'rfc3164'
                ]
            ),
            forward_to=dict(),
            pool=dict(),
            protocol=dict(
                choices=['tcp', 'udp', 'ipfix', 'netflow-9']
            ),
            distribution=dict(
                choices=[
                    'adaptive',
                    'balanced',
                    'replicated',
                ]
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            address=dict(),
            port=dict(type='int'),
            transport_profile=dict(),
            server_ssl_profile=dict(),
            template_retransmit_interval=dict(type='int'),
            template_delete_delay=dict(type='int'),

            # Deprecated settings
            pool_settings=dict(
                type='dict',
                suboptions=dict(
                    pool=dict(),
                    protocol=dict(
                        choices=['tcp', 'udp']
                    ),
                    distribution=dict(
                        choices=[
                            'adaptive',
                            'balanced',
                            'replicated',
                        ]
                    )
                ),
                removed_in_version=2.12,
            ),
            syslog_settings=dict(
                type='dict',
                suboptions=dict(
                    syslog_format=dict(
                        choices=[
                            'bsd-syslog',
                            'syslog',
                            'legacy-bigip',
                            'rfc5424',
                            'rfc3164'
                        ]
                    ),
                    forward_to=dict()
                ),
                removed_in_version=2.12,
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['syslog_settings', 'syslog_format'],
            ['syslog_settings', 'forward_to'],

            ['pool_settings', 'pool'],
            ['pool_settings', 'protocol'],
            ['pool_settings', 'distribution'],
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()

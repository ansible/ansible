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

import os
import traceback

PYVCLOUD_IMP_ERR = None
try:
    from pyvcloud.vcloudair import VCA
    HAS_PYVCLOUD = True
except ImportError:
    PYVCLOUD_IMP_ERR = traceback.format_exc()
    HAS_PYVCLOUD = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

SERVICE_MAP = {'vca': 'ondemand', 'vchs': 'subscription', 'vcd': 'vcd'}
LOGIN_HOST = {'vca': 'vca.vmware.com', 'vchs': 'vchs.vmware.com'}

DEFAULT_SERVICE_TYPE = 'vca'
DEFAULT_VERSION = '5.7'


class VcaError(Exception):

    def __init__(self, msg, **kwargs):
        self.kwargs = kwargs
        super(VcaError, self).__init__(msg)


def vca_argument_spec():
    return dict(
        username=dict(type='str', aliases=['user'], required=True),
        password=dict(type='str', aliases=['pass', 'passwd'], required=True, no_log=True),
        org=dict(),
        service_id=dict(),
        instance_id=dict(),
        host=dict(),
        api_version=dict(default=DEFAULT_VERSION),
        service_type=dict(default=DEFAULT_SERVICE_TYPE, choices=SERVICE_MAP.keys()),
        vdc_name=dict(),
        gateway_name=dict(default='gateway'),
        validate_certs=dict(type='bool', default=True, aliases=['verify_certs'])
    )


class VcaAnsibleModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        argument_spec = vca_argument_spec()
        argument_spec.update(kwargs.get('argument_spec', dict()))
        kwargs['argument_spec'] = argument_spec

        super(VcaAnsibleModule, self).__init__(*args, **kwargs)

        if not HAS_PYVCLOUD:
            self.fail(missing_required_lib('pyvcloud'),
                      exception=PYVCLOUD_IMP_ERR)

        self._vca = self.create_instance()
        self.login()

        self._gateway = None
        self._vdc = None

    @property
    def vca(self):
        return self._vca

    @property
    def gateway(self):
        if self._gateway is not None:
            return self._gateway
        vdc_name = self.params['vdc_name']
        gateway_name = self.params['gateway_name']
        _gateway = self.vca.get_gateway(vdc_name, gateway_name)
        if not _gateway:
            raise VcaError('vca instance has no gateway named %s' % gateway_name)
        self._gateway = _gateway
        return _gateway

    @property
    def vdc(self):
        if self._vdc is not None:
            return self._vdc
        vdc_name = self.params['vdc_name']
        _vdc = self.vca.get_vdc(vdc_name)
        if not _vdc:
            raise VcaError('vca instance has no vdc named %s' % vdc_name)
        self._vdc = _vdc
        return _vdc

    def get_vapp(self, vapp_name):
        vapp = self.vca.get_vapp(self.vdc, vapp_name)
        if not vapp:
            raise VcaError('vca instance has no vapp named %s' % vapp_name)
        return vapp

    def get_vm(self, vapp_name, vm_name):
        vapp = self.get_vapp(vapp_name)
        children = vapp.me.get_Children()
        vms = [vm for vm in children.get_Vm() if vm.name == vm_name]
        try:
            return vms[0]
        except IndexError:
            raise VcaError('vapp has no vm named %s' % vm_name)

    def create_instance(self):
        service_type = self.params.get('service_type', DEFAULT_SERVICE_TYPE)
        if service_type == 'vcd':
            host = self.params['host']
        else:
            host = LOGIN_HOST[service_type]
        username = self.params['username']

        version = self.params.get('api_version')
        if service_type == 'vchs':
            version = '5.6'

        verify = self.params.get('validate_certs')

        return VCA(host=host, username=username,
                   service_type=SERVICE_MAP[service_type],
                   version=version, verify=verify)

    def login(self):
        service_type = self.params['service_type']
        password = self.params['password']

        login_org = None
        if service_type == 'vcd':
            login_org = self.params['org']

        if not self.vca.login(password=password, org=login_org):
            self.fail('Login to VCA failed', response=self.vca.response.content)

        try:
            method_name = 'login_%s' % service_type
            meth = getattr(self, method_name)
            meth()
        except AttributeError:
            self.fail('no login method exists for service_type %s' % service_type)
        except VcaError as e:
            self.fail(e.message, response=self.vca.response.content, **e.kwargs)

    def login_vca(self):
        instance_id = self.params['instance_id']
        if not instance_id:
            raise VcaError('missing required instance_id for service_type vca')
        self.vca.login_to_instance_sso(instance=instance_id)

    def login_vchs(self):
        service_id = self.params['service_id']
        if not service_id:
            raise VcaError('missing required service_id for service_type vchs')

        org = self.params['org']
        if not org:
            raise VcaError('missing required org for service_type vchs')

        self.vca.login_to_org(service_id, org)

    def login_vcd(self):
        org = self.params['org']
        if not org:
            raise VcaError('missing required org for service_type vcd')

        if not self.vca.token:
            raise VcaError('unable to get token for service_type vcd')

        if not self.vca.vcloud_session.org_url:
            raise VcaError('unable to get org_url for service_type vcd')

        self.vca.login(token=self.vca.token, org=org,
                       org_url=self.vca.vcloud_session.org_url)

    def save_services_config(self, blocking=True):
        task = self.gateway.save_services_configuration()
        if not task:
            self.fail(msg='unable to save gateway services configuration')
        if blocking:
            self.vca.block_until_completed(task)

    def fail(self, msg, **kwargs):
        self.fail_json(msg=msg, **kwargs)

    def exit(self, **kwargs):
        self.exit_json(**kwargs)


# -------------------------------------------------------------
# 9/18/2015 @privateip
# All of the functions below here were migrated from the original
# vca_* modules.  All functions below should be considered deprecated
# and will be removed once all of the vca_* modules have been updated
# to use the new instance module above
# -------------------------------------------------------------

VCA_REQ_ARGS = ['instance_id', 'vdc_name']
VCHS_REQ_ARGS = ['service_id']
VCD_REQ_ARGS = []


def _validate_module(module):
    if not HAS_PYVCLOUD:
        module.fail_json(msg=missing_required_lib("pyvcloud"),
                         exception=PYVCLOUD_IMP_ERR)

    service_type = module.params.get('service_type', DEFAULT_SERVICE_TYPE)

    if service_type == 'vca':
        for arg in VCA_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json(msg="argument %s is mandatory when service type "
                                     "is vca" % arg)

    if service_type == 'vchs':
        for arg in VCHS_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json(msg="argument %s is mandatory when service type "
                                     "is vchs" % arg)

    if service_type == 'vcd':
        for arg in VCD_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json(msg="argument %s is mandatory when service type "
                                     "is vcd" % arg)


def serialize_instances(instance_list):
    instances = []
    for i in instance_list:
        instances.append(dict(apiUrl=i['apiUrl'], instance_id=i['id']))
    return instances


def _vca_login(vca, password, instance):
    if not vca.login(password=password):
        raise VcaError("Login Failed: Please check username or password",
                       error=vca.response.content)

    if not vca.login_to_instance_sso(instance=instance):
        s_json = serialize_instances(vca.instances)
        raise VcaError("Login to Instance failed: Seems like instance_id provided "
                       "is wrong .. Please check", valid_instances=s_json)

    return vca


def _vchs_login(vca, password, service, org):
    if not vca.login(password=password):
        raise VcaError("Login Failed: Please check username or password",
                       error=vca.response.content)

    if not vca.login_to_org(service, org):
        raise VcaError("Failed to login to org, Please check the orgname",
                       error=vca.response.content)


def _vcd_login(vca, password, org):
    # TODO: this function needs to be refactored
    if not vca.login(password=password, org=org):
        raise VcaError("Login Failed: Please check username or password "
                       "or host parameters")

    if not vca.login(password=password, org=org):
        raise VcaError("Failed to get the token",
                       error=vca.response.content)

    if not vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url):
        raise VcaError("Failed to login to org", error=vca.response.content)


def vca_login(module):
    service_type = module.params.get('service_type')
    username = module.params.get('username')
    password = module.params.get('password')
    instance = module.params.get('instance_id')
    org = module.params.get('org')
    vdc_name = module.params.get('vdc_name')
    service = module.params.get('service_id')
    version = module.params.get('api_version')
    verify = module.params.get('validate_certs')

    _validate_module(module)

    if not vdc_name and service_type == 'vchs':
        vdc_name = module.params.get('service_id')

    if not org and service_type == 'vchs':
        org = vdc_name or service

    if service_type == 'vcd':
        host = module.params.get('host')
    else:
        host = LOGIN_HOST[service_type]

    username = os.environ.get('VCA_USER', username)
    password = os.environ.get('VCA_PASS', password)

    if not username or not password:
        msg = "Either the username or password is not set, please check args"
        module.fail_json(msg=msg)

    if service_type == 'vchs':
        version = '5.6'
    elif service_type == 'vcd' and not version:
        version = '5.6'

    vca = VCA(host=host, username=username,
              service_type=SERVICE_MAP[service_type],
              version=version, verify=verify)

    try:
        if service_type == 'vca':
            _vca_login(vca, password, instance)
        elif service_type == 'vchs':
            _vchs_login(vca, password, service, org)
        elif service_type == 'vcd':
            _vcd_login(vca, password, org)
    except VcaError as e:
        module.fail_json(msg=e.message, **e.kwargs)

    return vca

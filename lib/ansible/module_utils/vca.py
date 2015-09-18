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

try:
    from pyvcloud.vcloudair import VCA
    HAS_PYVCLOUD = True
except ImportError:
    HAS_PYVCLOUD = False

SERVICE_MAP = {'vca': 'ondemand', 'vchs': 'subscription', 'vcd': 'vcd'}
LOGIN_HOST = {'vca': 'vca.vmware.com', 'vchs': 'vchs.vmware.com'}
VCA_REQ_ARGS = ['instance_id', 'vdc_name']
VCHS_REQ_ARGS = ['service_id']
DEFAULT_SERVICE_TYPE = 'vca'

class VcaError(Exception):

    def __init__(self, msg, **kwargs):
        self.kwargs = kwargs
        super(VcaError, self).__init__(msg)

def _validate_module(module):
    if not HAS_PYVCLOUD:
        module.fail_json("python module pyvcloud is needed for this module")

    service_type = module.params.get('service_type', DEFAULT_SERVICE_TYPE)

    if service_type == 'vca':
        for arg in VCA_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json("argument %s is mandatory when service type "
                                 "is vca" % arg)

    if service_type == 'vchs':
        for arg in VCHS_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json("argument %s is mandatory when service type "
                                 "is vchs" % arg)

    if service_type == 'vcd':
        for arg in VCD_REQ_ARGS:
            if module.params.get(arg) is None:
                module.fail_json("argument %s is mandatory when service type "
                                 "is vcd" % arg)


def serialize_instances(instance_list):
    instances = []
    for i in instance_list:
        instances.append(dict(apiUrl=i['apiUrl'], instance_id=i['id']))
    return instances

def vca_argument_spec():
    return dict(
        username = dict(default=None),
        password = dict(default=None),
        org = dict(default=None),
        service_id = dict(default=None),
        instance_id = dict(default=None),
        host = dict(default=None),
        api_version = dict(default='5.7'),
        service_type = dict(default='vca', choices=['vchs', 'vca', 'vcd']),
        vdc_name = dict(default=None),
    )

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
    verify = module.params.get('verify_certs')

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
        version == '5.6'

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
    except VcaError, e:
        module.fail_json(msg=e.message, **e.kwargs)

    return vca


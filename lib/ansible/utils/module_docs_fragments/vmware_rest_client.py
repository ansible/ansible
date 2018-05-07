# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for VMware REST Client based modules
    DOCUMENTATION = '''
options:
  hostname:
    description:
    - The hostname or IP address of the vSphere vCenter server.
    - If the value is not specified in the task, the value of environment variable C(VMWARE_HOST) will be used instead.
    required: False
  username:
    description:
    - The username of the vSphere vCenter server.
    - If the value is not specified in the task, the value of environment variable C(VMWARE_USER) will be used instead.
    aliases: ['user', 'admin']
  password:
    description:
    - The password of the vSphere vCenter server.
    - If the value is not specified in the task, the value of environment variable C(VMWARE_PASSWORD) will be used instead.
    required: False
    aliases: ['pass', 'pwd']
  validate_certs:
    description:
    - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
    - If the value is not specified in the task, the value of environment variable C(VMWARE_VALIDATE_CERTS) will be used instead.
    default: True
    type: bool
    required: False
  protocol:
    description:
    - The connection to protocol.
    choices: ['https', 'http']
    default: 'https'
    required: False
'''

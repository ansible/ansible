# Copyright: (c) 2016, Charles Paul <cpaul@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for VMware modules
    DOCUMENTATION = '''
options:
    hostname:
      description:
      - The hostname or IP address of the vSphere vCenter or ESXi server.
      - If the value is not specified in the task, the value of environment variable C(VMWARE_HOST) will be used instead.
      - Environment variable supported added in version 2.6.
      required: False
    username:
      description:
      - The username of the vSphere vCenter or ESXi server.
      - If the value is not specified in the task, the value of environment variable C(VMWARE_USER) will be used instead.
      - Environment variable supported added in version 2.6.
      required: False
      aliases: ['user', 'admin']
    password:
      description:
      - The password of the vSphere vCenter or ESXi server.
      - If the value is not specified in the task, the value of environment variable C(VMWARE_PASSWORD) will be used instead.
      - Environment variable supported added in version 2.6.
      required: False
      aliases: ['pass', 'pwd']
    validate_certs:
      description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
      - If the value is not specified in the task, the value of environment variable C(VMWARE_VALIDATE_CERTS) will be used instead.
      - Environment variable supported added in version 2.6.
      - If set to C(True), please make sure Python >= 2.7.9 is installed on the given machine.
      default: 'True'
      type: bool
    port:
      description:
      - The port number of the vSphere vCenter or ESXi server.
      - If the value is not specified in the task, the value of environment variable C(VMWARE_PORT) will be used instead.
      - Environment variable supported added in version 2.6.
      required: False
      default: 443
      version_added: 2.5
'''

# Copyright: (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for XenServer modules
    DOCUMENTATION = '''
options:
    hostname:
      description:
      - The hostname or IP address of the XenServer host or XenServer pool master.
      - If the value is not specified in the task, the value of environment variable C(XENSERVER_HOST) will be used instead.
      required: False
      default: 'localhost'
      aliases: ['host', 'pool']
    username:
      description:
      - The username to use for connecting to XenServer.
      - If the value is not specified in the task, the value of environment variable C(XENSERVER_USER) will be used instead.
      required: False
      default: 'root'
      aliases: ['user', 'admin']
    password:
      description:
      - The password to use for connecting to XenServer.
      - If the value is not specified in the task, the value of environment variable C(XENSERVER_PASSWORD) will be used instead.
      required: False
      aliases: ['pass', 'pwd']
    validate_certs:
      description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
      - If the value is not specified in the task, the value of environment variable C(XENSERVER_VALIDATE_CERTS) will be used instead.
      default: 'yes'
      type: bool
'''

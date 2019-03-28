# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Charles Paul <cpaul@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for VCA modules
    DOCUMENTATION = r'''
options:
    username:
      description:
        - The vca username or email address, if not set the environment variable C(VCA_USER) is checked for the username.
      type: str
      aliases: [ user ]
    password:
      description:
        - The vca password, if not set the environment variable C(VCA_PASS) is checked for the password.
      type: str
      aliases: [ pass, passwd]
    org:
      description:
        - The org to login to for creating vapp.
        - This option is required when the C(service_type) is I(vdc).
      type: str
    instance_id:
      description:
        - The instance ID in a vchs environment to be used for creating the vapp.
      type: str
    host:
      description:
        - The authentication host to be used when service type is vcd.
      type: str
    api_version:
      description:
        - The API version to be used with the vca.
      type: str
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against.
      type: str
      choices: [ vca, vcd, vchs ]
      default: vca
    state:
      description:
        - Whether the object should be added or removed.
      type: str
      choices: [ absent, present ]
      default: present
    validate_certs:
      description:
        - If the certificates of the authentication is to be verified.
      type: bool
      default: yes
      aliases: [ verify_certs ]
    vdc_name:
      description:
        - The name of the vdc where the gateway is located.
      type: str
    gateway_name:
      description:
        - The name of the gateway of the vdc where the rule should be added.
      type: str
      default: gateway
'''

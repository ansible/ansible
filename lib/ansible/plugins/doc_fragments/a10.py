# -*- coding: utf-8 -*-

# Copyright: (c) 2016, John Barker <jobarker@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description:
      - Hostname or IP of the A10 Networks device.
    type: str
    required: true
  username:
    description:
      - An account with administrator privileges.
    type: str
    required: true
    aliases: [ admin, user ]
  password:
    description:
      - Password for the C(username) account.
    type: str
    required: true
    aliases: [ pass, pwd ]
  write_config:
    description:
      - If C(yes), any changes will cause a write of the running configuration
        to non-volatile memory. This will save I(all) configuration changes,
        including those that may have been made manually or through other modules,
        so care should be taken when specifying C(yes).
    type: bool
    default: no
    version_added: '2.2'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only be used on personally controlled devices using self-signed certificates.
    type: bool
    default: yes
    version_added: '2.2'
notes:
    - Requires A10 Networks aXAPI 2.1.
'''

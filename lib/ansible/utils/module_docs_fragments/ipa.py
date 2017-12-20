# Copyright (c) 2017, Ansible Project
# Copyright (c) 2017, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for FreeIPA/IPA modules
    DOCUMENTATION = '''
options:
  ipa_port:
    description: Port of IPA server
    default: 443
  ipa_host:
    description: IP or hostname of IPA server
    default: ipa.example.com
  ipa_user:
    description: Administrative account used on IPA server
    default: admin
  ipa_pass:
    description: Password of administrative user
    required: true
  ipa_prot:
    description: Protocol used by IPA server
    default: https
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    default: true

'''

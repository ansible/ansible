# Copyright (c) 2017-18, Ansible Project
# Copyright (c) 2017-18, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for FreeIPA/IPA modules
    DOCUMENTATION = '''
options:
  ipa_port:
    description:
    - Port of FreeIPA / IPA server.
    - If the value is not specified in the task, the value of environment variable C(IPA_PORT) will be used instead.
    - If both the environment variable C(IPA_PORT) and the value are not specified in the task, then default value is set.
    - 'Environment variable fallback mechanism is added in version 2.5.'
    default: 443
  ipa_host:
    description:
    - IP or hostname of IPA server.
    - If the value is not specified in the task, the value of environment variable C(IPA_HOST) will be used instead.
    - If both the environment variable C(IPA_HOST) and the value are not specified in the task, then default value is set.
    - 'Environment variable fallback mechanism is added in version 2.5.'
    default: ipa.example.com
  ipa_user:
    description:
    - Administrative account used on IPA server.
    - If the value is not specified in the task, the value of environment variable C(IPA_USER) will be used instead.
    - If both the environment variable C(IPA_USER) and the value are not specified in the task, then default value is set.
    - 'Environment variable fallback mechanism is added in version 2.5.'
    default: admin
  ipa_pass:
    description:
    - Password of administrative user.
    - If the value is not specified in the task, the value of environment variable C(IPA_PASS) will be used instead.
    - If both the environment variable C(IPA_PASS) and the value are not specified in the task, then default value is set.
    - 'Environment variable fallback mechanism is added in version 2.5.'
    required: true
  ipa_prot:
    description:
    - Protocol used by IPA server.
    - If the value is not specified in the task, the value of environment variable C(IPA_PROT) will be used instead.
    - If both the environment variable C(IPA_PROT) and the value are not specified in the task, then default value is set.
    - 'Environment variable fallback mechanism is added in version 2.5.'
    default: https
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    default: true

'''

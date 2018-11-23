# Copyright: (c) 2018, Davide Blasi (@davegararh)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for Sapcewalk modules
    DOCUMENTATION = '''
options:
    url:
      description:
      - The full URL to the Spacewalk API.
      type: str
      required: true
    login:
      description:
      - Spacewalk login.
      type: str
      required: true
    password:
      description:
      - Spacewalk password.
      required: true
    validate_certs:
      description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
      - If the value is not specified in the task, the value of environment variable C(SPACEWALK_VALIDATE_CERTS) will be used instead.
      - Environment variable supported added in version 2.6.
      - If set to C(yes), please make sure Python >= 2.7.9 is installed on the given machine.
      type: bool
      default: 'yes'
'''

# Copyright: (c) 2018, Davide Blasi (@davegararh)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for Sapcewalk modules
    DOCUMENTATION = '''
options:
    url:
      description:
      - The full URL to the Spacewalk API such as
      - C(https://spacewalk.example.net/rpc/api)
      - you can use eviroment variable C(SPACEWALK_URL)
      type: str
      required: true
    login:
      description:
      - Spacewalk login.
      - you can use eviroment variable C(SPACEWALK_LOGIN)
      type: str
      required: true
    password:
      description:
      - Spacewalk password.
      - you can use eviroment variable C(SPACEWALK_PASSWORD)
      required: true
    validate_certs:
      description:
      - If set to C(yes), please make sure Python >= 2.7.9 is installed on the given machine.
      - you can use eviroment variable C(SPACEWALK_VALIDATE_CERTS)
      type: bool
      default: 'yes'
'''

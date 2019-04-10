#
# Copyright: (c) 2019, Sandeep Kasargod <sandeep@vexata.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
    - See respective platform section for more details
requirements:
    - See respective platform section for more details
notes:
    - Ansible modules are available for Vexata VX100 arrays.
'''

    # Documentation fragment for Vexata VX100 series
    VX100 = r'''
options:
  array:
    description:
      - Vexata VX100 array hostname or IPv4 Address.
    required: true
    type: str
  user:
    description:
      - Vexata API user with administrative privileges.
    required: false
    type: str
  password:
    description:
      - Vexata API user password.
    required: false
    type: str
  validate_certs:
    description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
      - If set to C(yes), please make sure Python >= 2.7.9 is installed on the given machine.
    required: false
    type: bool
    default: 'no'

requirements:
  - Vexata VX100 storage array with VXOS >= v3.5.0 on storage array
  - vexatapi >= 0.0.1
  - python >= 2.7
  - VEXATA_USER and VEXATA_PASSWORD environment variables must be set if
    user and password arguments are not passed to the module directly.
'''

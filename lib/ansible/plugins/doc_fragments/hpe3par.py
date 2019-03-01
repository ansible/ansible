# Copyright: (c) 2018, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # HPE 3PAR doc fragment
    DOCUMENTATION = '''
options:
    storage_system_ip:
      description:
        - The storage system IP address.
      type: str
      required: true
    storage_system_password:
      description:
        - The storage system password.
      type: str
      required: true
    storage_system_username:
      description:
        - The storage system user name.
      type: str
      required: true

requirements:
  - hpe3par_sdk >= 1.0.2. Install using 'pip install hpe3par_sdk'
  - WSAPI service should be enabled on the 3PAR storage array.
notes:
  -  check_mode not supported
    '''

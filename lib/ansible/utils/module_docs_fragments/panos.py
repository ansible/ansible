# -*- coding: utf-8 -*-

# Copyright: (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
# Copyright: (c) 2018, Kevin Breit (@kbreit)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = '''
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device.
        required: true
    password:
        description:
            - Password for authentication.
        required: true
    username:
        description:
            - Username for authentication.
        default: "admin"
'''

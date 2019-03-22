# -*- coding: utf-8 -*-

# Copyright: (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
# Copyright: (c) 2018, Kevin Breit (@kbreit)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device.
        type: str
        required: true
    password:
        description:
            - Password for authentication.
        type: str
        required: true
    username:
        description:
            - Username for authentication.
        type: str
        default: admin
'''

    PROVIDER = r'''
options:
    provider:
        description:
            - A dict object containing connection details.
        version_added: '2.8'
        required: true
        suboptions:
            ip_address:
                description:
                    - The IP address or hostname of the PAN-OS device being configured.
                type: str
                required: true
            username:
                description:
                    - The username to use for authentication.  This is ignored if
                      I(api_key) is specified.
                type: str
                default: 'admin'
            password:
                description:
                    - The password to use for authentication.  This is ignored if
                      I(api_key) is specified.
                type: str
            api_key:
                description:
                    - The API key to use instead of generating it using
                      I(username) / I(password).
                type: str
            port:
                description:
                    - The port number to connect to the PAN-OS device on.
                type: int
                default: 443
            serial_number:
                description:
                    - The serial number of a firewall to use for targeted commands.
                      If I(ip_address) is not a Panorama PAN-OS device, then
                      this param is ignored.
                type: str
'''

    TRANSITIONAL_PROVIDER = r'''
options:
    provider:
        description:
            - A dict object containing connection details.
        version_added: '2.8'
        suboptions:
            ip_address:
                description:
                    - The IP address or hostname of the PAN-OS device being configured.
                type: str
            username:
                description:
                    - The username to use for authentication.  This is ignored if
                      I(api_key) is specified.
                type: str
                default: 'admin'
            password:
                description:
                    - The password to use for authentication.  This is ignored if
                      I(api_key) is specified.
                type: str
            api_key:
                description:
                    - The API key to use instead of generating it using
                      I(username) / I(password).
                type: str
            port:
                description:
                    - The port number to connect to the PAN-OS device on.
                type: int
                default: 443
            serial_number:
                description:
                    - The serial number of a firewall to use for targeted commands.
                      If I(ip_address) is not a Panorama PAN-OS device, then
                      this param is ignored.
                type: str
    ip_address:
        description:
            - B(Deprecated)
            - Use I(provider) to specify PAN-OS connectivity instead.
            - HORIZONTALLINE
            - The IP address or hostname of the PAN-OS device being configured.
        type: str
    username:
        description:
            - B(Deprecated)
            - Use I(provider) to specify PAN-OS connectivity instead.
            - HORIZONTALLINE
            - The username to use for authentication.  This is ignored if
              I(api_key) is specified.
        type: str
        default: 'admin'
    password:
        description:
            - B(Deprecated)
            - Use I(provider) to specify PAN-OS connectivity instead.
            - HORIZONTALLINE
            - The password to use for authentication.  This is ignored if
              I(api_key) is specified.
        type: str
    api_key:
        description:
            - B(Deprecated)
            - Use I(provider) to specify PAN-OS connectivity instead.
            - HORIZONTALLINE
            - The API key to use instead of generating it using
              I(username) / I(password).
        type: str
    port:
        description:
            - B(Deprecated)
            - Use I(provider) to specify PAN-OS connectivity instead.
            - HORIZONTALLINE
            - The port number to connect to the PAN-OS device on.
        type: int
        default: 443
notes:
    - PAN-OS connectivity should be specified using I(provider) or the
      classic PAN-OS connectivity params (I(ip_address), I(username),
      I(password), I(api_key), and I(port)).  If both are present, then the
      classic params are ignored.
'''

    STATE = r'''
options:
    state:
        description:
            - The state.
        type: str
        default: present
        choices:
            - present
            - absent
'''

    RULEBASE = r'''
options:
    rulebase:
        description:
            - The rulebase in which the rule is to exist.  If left unspecified,
              this defaults to I(rulebase=pre-rulebase) for Panorama.  For
              NGFW, this is always set to be I(rulebase=rulebase).
        type: str
        choices:
            - pre-rulebase
            - rulebase
            - post-rulebase
'''

    VSYS_DG = r'''
options:
    vsys_dg:
        description:
            - The vsys (for NGFW) or device group (for Panorama) this
              operation should target.  If left unspecified, this defaults to
              I(vsys_dg=vsys1) for NGFW or I(vsys_dg=shared) for Panorama.
        type: str
'''

    DEVICE_GROUP = r'''
options:
    device_group:
        description:
            - (Panorama only) The device group the operation should target.
        type: str
        default: shared
'''

    VSYS_IMPORT = r'''
options:
    vsys:
        description:
            - The vsys this object should be imported into.  Objects that are
              imported include interfaces, virtual routers, virtual wires, and
              VLANs.  Interfaces are typically imported into vsys1 if no vsys
              is specified.
        type: str
'''

    VSYS = r'''
options:
    vsys:
        description:
            - The vsys this object belongs to.
        type: str
        default: vsys1
'''

    TEMPLATE_ONLY = r'''
options:
    template:
        description:
            - (Panorama only) The template this operation should target.  This
              param is required if the PAN-OS device is Panorama.
        type: str
'''

    FULL_TEMPLATE_SUPPORT = r'''
options:
    template:
        description:
            - (Panorama only) The template this operation should target.
              Mutually exclusive with I(template_stack).
        type: str
    template_stack:
        description:
            - (Panorama only) The template stack this operation should target.
              Mutually exclusive with I(template).
        type: str
notes:
    - If the PAN-OS to be configured is Panorama, either I(template) or
      I(template_stack) must be specified.
'''

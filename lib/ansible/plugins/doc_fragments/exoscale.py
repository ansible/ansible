# -*- coding: utf-8 -*-

# Copyright: (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard exoscale documentation fragment
    DOCUMENTATION = r'''
options:
  api_key:
    description:
      - API key of the Exoscale DNS API.
      - Since 2.4, the ENV variable C(CLOUDSTACK_KEY) is used as default, when defined.
    type: str
  api_secret:
    description:
      - Secret key of the Exoscale DNS API.
      - Since 2.4, the ENV variable C(CLOUDSTACK_SECRET) is used as default, when defined.
    type: str
  api_timeout:
    description:
      - HTTP timeout to Exoscale DNS API.
      - Since 2.4, the ENV variable C(CLOUDSTACK_TIMEOUT) is used as default, when defined.
    type: int
    default: 10
  api_region:
    description:
      - Name of the ini section in the C(cloustack.ini) file.
      - Since 2.4, the ENV variable C(CLOUDSTACK_REGION) is used as default, when defined.
    type: str
    default: cloudstack
  validate_certs:
    description:
      - Validate SSL certs of the Exoscale DNS API.
    type: bool
    default: yes
requirements:
  - python >= 2.6
notes:
  - As Exoscale DNS uses the same API key and secret for all services, we reuse the config used for Exscale Compute based on CloudStack.
    The config is read from several locations, in the following order.
    The C(CLOUDSTACK_KEY), C(CLOUDSTACK_SECRET) environment variables.
    A C(CLOUDSTACK_CONFIG) environment variable pointing to an C(.ini) file,
    A C(cloudstack.ini) file in the current working directory.
    A C(.cloudstack.ini) file in the users home directory.
    Optionally multiple credentials and endpoints can be specified using ini sections in C(cloudstack.ini).
    Use the argument C(api_region) to select the section name, default section is C(cloudstack).
  - This module does not support multiple A records and will complain properly if you try.
  - More information Exoscale DNS can be found on https://community.exoscale.ch/documentation/dns/.
  - This module supports check mode and diff.
'''

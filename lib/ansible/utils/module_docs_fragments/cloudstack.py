# -*- coding: utf-8 -*-
# Copyright (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard cloudstack documentation fragment
    DOCUMENTATION = '''
options:
  api_key:
    description:
      - API key of the CloudStack API.
  api_secret:
    description:
      - Secret key of the CloudStack API.
  api_url:
    description:
      - URL of the CloudStack API e.g. https://cloud.example.com/client/api.
  api_http_method:
    description:
      - HTTP method used.
    default: get
    choices: [ get, post ]
  api_timeout:
    description:
      - HTTP timeout.
    default: 10
  api_region:
    description:
      - Name of the ini section in the C(cloustack.ini) file.
    default: cloudstack
requirements:
  - "python >= 2.6"
  - "cs >= 0.6.10"
notes:
  - Ansible uses the C(cs) library's configuration method if credentials are not
    provided by the arguments C(api_url), C(api_key), C(api_secret).
    Configuration is read from several locations, in the following order:
    The C(CLOUDSTACK_ENDPOINT), C(CLOUDSTACK_KEY), C(CLOUDSTACK_SECRET) and
    C(CLOUDSTACK_METHOD). C(CLOUDSTACK_TIMEOUT) environment variables.
    A C(CLOUDSTACK_CONFIG) environment variable pointing to an C(.ini) file.
    A C(cloudstack.ini) file in the current working directory.
    A C(.cloudstack.ini) file in the users home directory.
    Optionally multiple credentials and endpoints can be specified using ini sections in C(cloudstack.ini).
    Use the argument C(api_region) to select the section name, default section is C(cloudstack).
    See https://github.com/exoscale/cs for more information.
  - A detailed guide about cloudstack modules can be found on http://docs.ansible.com/ansible/guide_cloudstack.html.
  - This module supports check mode.
'''

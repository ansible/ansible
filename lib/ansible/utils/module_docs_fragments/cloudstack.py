# -*- coding: utf-8 -*-
# Copyright (c) 2015 René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):

    # Standard cloudstack documentation fragment
    DOCUMENTATION = '''
options:
  api_key:
    description:
      - API key of the CloudStack API.
    required: false
    default: null
  api_secret:
    description:
      - Secret key of the CloudStack API.
    required: false
    default: null
  api_url:
    description:
      - URL of the CloudStack API e.g. https://cloud.example.com/client/api.
    required: false
    default: null
  api_http_method:
    description:
      - HTTP method used.
    required: false
    default: 'get'
    choices: [ 'get', 'post' ]
  api_timeout:
    description:
      - HTTP timeout.
    required: false
    default: 10
  api_region:
    description:
      - Name of the ini section in the C(cloustack.ini) file.
    required: false
    default: cloudstack
requirements:
  - "python >= 2.6"
  - "cs >= 0.6.10"
notes:
  - Ansible uses the C(cs) library's configuration method if credentials are not
    provided by the arguments C(api_url), C(api_key), C(api_secret).
    Configuration is read from several locations, in the following order.
    - The C(CLOUDSTACK_ENDPOINT), C(CLOUDSTACK_KEY), C(CLOUDSTACK_SECRET) and
      C(CLOUDSTACK_METHOD). C(CLOUDSTACK_TIMEOUT) environment variables.
    - A C(CLOUDSTACK_CONFIG) environment variable pointing to an C(.ini) file,
    - A C(cloudstack.ini) file in the current working directory.
    - A C(.cloudstack.ini) file in the users home directory.
    Optionally multiple credentials and endpoints can be specified using ini sections in C(cloudstack.ini).
    Use the argument C(api_region) to select the section name, default section is C(cloudstack).
    See https://github.com/exoscale/cs for more information.
  - This module supports check mode.
'''

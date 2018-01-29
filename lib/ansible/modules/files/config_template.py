# Copyright: (c) 2015, Kevin Carter <kevin.carter@rackspace.com>
# Copyright: (c) 2018, Jean-Philippe Evrard <jean-philippe@evrard.me>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: config_template
version_added: 2.5
short_description: Renders template files providing a create/update override interface
description:
  - The module contains the template functionality with the ability to override items
    in config, in transit, through the use of a simple dictionary without having to
    write out various temp files on target machines, or running multiple tasks.
  - The module renders all of the potential jinja a user could provide in both the
    template file and in the override dictionary which is ideal for deployers who may
    have lots of different configs using a similar code base.
  - The module respects comments existing in the source/destination file wherever
    possible.
  - The module is valid for ini, json, and yaml file types.
  - The module is an extension of the **copy** module and all of attributes that can be
    set there are available to be set here.
options:
  src:
    description:
      - Path of a Jinja2 formatted template on the local server. This can be a relative
        or absolute path.
    required: true
    default: null
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
    default: null
  config_overrides:
    description:
      - A dictionary used to update or override items within a configuration template.
        The dictionary data structure may be nested. If the target config file is an ini
        file the nested keys in the ``config_overrides`` will be used as section
        headers.
  config_type:
    description:
      - A string value describing the target config type.
    choices:
      - ini
      - json
      - yaml
  list_extend:
    description:
      - By default a list item in a JSON or YAML format will extend if
        its already defined in the target template and a config_override
        using a list is being set for the existing "key". This functionality
        can be toggled on or off using this option. If disabled an override
        list will replace an existing "key".
    choices:
      - True
      - False
  ignore_none_type:
    description:
      - Can be true or false. If ignore_none_type is set to true, then
        valueless INI options will not be written out to the resultant file.
        If it's set to false, then config_template will write out only
        the option name without the '=' or ':' suffix. The default is true.
    choices:
      - True
      - False

author: Kevin Carter
"""

EXAMPLES = """
  - name: run config template ini
    config_template:
      src: templates/test.ini.j2
      dest: /tmp/test.ini
      config_overrides: {}
      config_type: ini

  - name: run config template json
    config_template:
      src: templates/test.json.j2
      dest: /tmp/test.json
      config_overrides: {}
      config_type: json

  - name: run config template yaml
    config_template:
      src: templates/test.yaml.j2
      dest: /tmp/test.yaml
      config_overrides: {}
      config_type: yaml
"""

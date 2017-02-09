# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Dimension Data
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Adam Friedman  <tintoy@tintoy.io>


class ModuleDocFragment(object):

    # Dimension Data doc fragment
    DOCUMENTATION = '''

options:
  region:
    description:
      - The target region.
    choices:
      - Regions are defined in Apache libcloud project [libcloud/common/dimensiondata.py]
      - They are also listed in U(https://libcloud.readthedocs.io/en/latest/compute/drivers/dimensiondata.html)
      - Note that the default value "na" stands for "North America".
      - The module prepends 'dd-' to the region choice.
    default: na
  mcp_user:
    description:
      - The username used to authenticate to the CloudControl API.
      - If not specified, will fall back to C(MCP_USER) from environment variable or C(~/.dimensiondata).
    required: false
  mcp_password:
    description:
      - The password used to authenticate to the CloudControl API.
      - If not specified, will fall back to C(MCP_PASSWORD) from environment variable or C(~/.dimensiondata).
      - Required if I(mcp_user) is specified.
    required: false
  location:
    description:
      - The target datacenter.
    required: true
  validate_certs:
    description:
      - If C(false), SSL certificates will not be validated.
      - This should only be used on private instances of the CloudControl API that use self-signed certificates.
    required: false
    default: true
    '''

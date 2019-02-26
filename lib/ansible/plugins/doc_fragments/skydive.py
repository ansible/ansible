#
# (c) 2019, Sumit Jaiswal (@sjaiswal)
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

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  provider:
    description:
      - A dict object containing connection details.
    suboptions:
      endpoint:
        description:
          - Specifies the hostname/address along with the port as C(localhost:8082)for
            connecting to the remote instance of SKYDIVE client over the REST API.
        required: true
      user:
        description:
          - Configures the username to use to authenticate the connection to
            the remote instance of SKYDIVE client.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote instance of SKYDIVE client.
      insecure:
        description:
          - Ignore SSL certification verification.
        type: bool
        default: false
      ssl:
        description:
          - Specifies the ssl parameter that decides if the connection type shall be
            http or https.
        type: bool
        default: false
notes:
  - "This module must be run locally, which can be achieved by specifying C(connection: local)."
"""

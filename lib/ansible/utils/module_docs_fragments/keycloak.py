# Copyright (c) 2017 Eike Frost <ei@kefro.st>
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

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
    auth_keycloak_url:
        description:
            - URL to the Keycloak instance.
        required: true
        aliases:
          - url

    auth_client_id:
        description:
            - OpenID Connect I(client_id) to authenticate to the API with.
        default: admin-cli
        required: true

    auth_realm:
        description:
            - Keycloak realm name to authenticate to for API access.
        required: true

    auth_client_secret:
        description:
            - Client Secret to use in conjunction with I(auth_client_id) (if required).

    auth_username:
        description:
            - Username to authenticate for API access with.
        required: true
        aliases:
          - username

    auth_password:
        description:
            - Password to authenticate for API access with.
        required: true
        aliases:
          - password

    validate_certs:
        description:
            - Verify TLS certificates (do not disable this in production).
        default: True
        type: bool
'''

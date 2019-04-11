# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Eike Frost <ei@kefro.st>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
options:
    auth_keycloak_url:
        description:
            - URL to the Keycloak instance.
        type: str
        required: true
        aliases:
          - url

    auth_client_id:
        description:
            - OpenID Connect I(client_id) to authenticate to the API with.
        type: str
        default: admin-cli
        required: true

    auth_realm:
        description:
            - Keycloak realm name to authenticate to for API access.
        type: str
        required: true

    auth_client_secret:
        description:
            - Client Secret to use in conjunction with I(auth_client_id) (if required).
        type: str

    auth_username:
        description:
            - Username to authenticate for API access with.
        type: str
        required: true
        aliases:
          - username

    auth_password:
        description:
            - Password to authenticate for API access with.
        type: str
        required: true
        aliases:
          - password

    validate_certs:
        description:
            - Verify TLS certificates (do not disable this in production).
        type: bool
        default: yes
'''

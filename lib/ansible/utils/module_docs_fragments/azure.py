# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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
#


class ModuleDocFragment(object):

    # Azure doc fragment
    DOCUMENTATION = '''

options:
    ad_user:
        description:
            - Active Directory username. Use when authenticating with an Active Directory user rather than service
              principal.
        required: false
        default: null
    password:
        description:
            - Active Directory user password. Use when authenticating with an Active Directory user rather than service
              principal.
        required: false
        default: null
    profile:
        description:
            - Security profile found in ~/.azure/credentials file.
        required: false
        default: null
    subscription_id:
        description:
            - Your Azure subscription Id.
        required: false
        default: null
    client_id:
        description:
            - Azure client ID. Use when authenticating with a Service Principal.
        required: false
        default: null
    secret:
        description:
            - Azure client secret. Use when authenticating with a Service Principal.
        required: false
        default: null
    tenant:
        description:
            - Azure tenant ID. Use when authenticating with a Service Principal.
        required: false
        default: null

requirements:
    - "python >= 2.7"
    - "azure == 2.0.0rc5"

notes:
    - For authentication with Azure you can pass parameters, set environment variables or use a profile stored
      in ~/.azure/credentials. Authentication is possible using a service principal or Active Directory user.
      To authenticate via service principal pass subscription_id, client_id, secret and tenant or set set environment
      variables AZURE_SUBSCRIPTION_ID, AZURE_CLIENT_ID, AZURE_SECRET and AZURE_TENANT.
    - To Authentication via Active Directory user pass ad_user and password, or set AZURE_AD_USER and
      AZURE_PASSWORD in the environment.
    - "Alternatively, credentials can be stored in ~/.azure/credentials. This is an ini file containing
      a [default] section and the following keys: subscription_id, client_id, secret and tenant or
      subscription_id, ad_user and password. It is also possible to add additional profiles. Specify the profile
      by passing profile or setting AZURE_PROFILE in the environment."
    '''

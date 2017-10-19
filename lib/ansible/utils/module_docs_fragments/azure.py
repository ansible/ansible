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
            - Security profile found in C(~/.azure/credentials) file.
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
    cloud_environment:
        description:
            - For cloud environments other than the US public cloud, the environment name (as defined by Azure Python SDK, eg, C(AzureChinaCloud),
              C(AzureUSGovernment)), or a metadata discovery endpoint URL (required for Azure Stack). Can also be set via credential file profile or
              the C(AZURE_CLOUD_ENVIRONMENT) environment variable.
        default: AzureCloud
requirements:
    - "python >= 2.7"
    - "azure >= 2.0.0"

notes:
    - For authentication with Azure you can pass parameters, set environment variables, use a profile stored
      in C(~/.azure/credentials) or login with Azure CLI.
      Authentication is possible using a service principal or Active Directory user.
      To authenticate via service principal, pass C(subscription_id), C(client_id), C(secret) and C(tenant) or set environment
      variables C(AZURE_SUBSCRIPTION_ID), C(AZURE_CLIENT_ID), C(AZURE_SECRET) and C(AZURE_TENANT).
    - To authenticate via Active Directory user, pass C(ad_user) and C(password), or set C(AZURE_AD_USER) and
      C(AZURE_PASSWORD) in the environment.
    - "Alternatively, credentials can be stored in C(~/.azure/credentials). This is an ini file containing
      a [default] section and the following keys: C(subscription_id), C(client_id), C(secret) and C(tenant) or
      C(subscription_id), C(ad_user) and C(password). It is also possible to add additional profiles. Specify the profile
      by passing profile or setting C(AZURE_PROFILE) in the environment."
    - Use 'az login' to login with Azure CLI.
    '''

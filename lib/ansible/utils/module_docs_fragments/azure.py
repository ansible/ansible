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
    password:
        description:
            - Active Directory user password. Use when authenticating with an Active Directory user rather than service
              principal.
    profile:
        description:
            - Security profile found in ~/.azure/credentials file.
    subscription_id:
        description:
            - Your Azure subscription Id.
    client_id:
        description:
            - Azure client ID. Use when authenticating with a Service Principal.
    secret:
        description:
            - Azure client secret. Use when authenticating with a Service Principal.
    tenant:
        description:
            - Azure tenant ID. Use when authenticating with a Service Principal.
    cloud_environment:
        description:
            - For cloud environments other than the US public cloud, the environment name (as defined by Azure Python SDK, eg, C(AzureChinaCloud),
              C(AzureUSGovernment)), or a metadata discovery endpoint URL (required for Azure Stack). Can also be set via credential file profile or
              the C(AZURE_CLOUD_ENVIRONMENT) environment variable.
        default: AzureCloud
        version_added: 2.4
    adfs_authority_url:
        description:
            - Azure AD authority url. Use when authenticating with Username/password, and has your own ADFS authority.
        required: false
        default: null
        version_added: 2.6
    cert_validation_mode:
        description:
            - Controls the certificate validation behavior for Azure endpoints. By default, all modules will validate the server certificate, but
              when an HTTPS proxy is in use, or against Azure Stack, it may be necessary to disable this behavior by passing C(ignore). Can also be
              set via credential file profile or the C(AZURE_CERT_VALIDATION) environment variable.
        choices: [validate, ignore]
        version_added: 2.5
    auth_source:
        description:
            - Controls the source of the credentials to use for authentication.
            - C(auto) will follow the default precedence of module parameters -> environment variables -> default profile in credential file
              C(~/.azure/credentials).
            - When set to C(cli), the credentials will be sources from the default Azure CLI profile.
            - Can also be set via the C(ANSIBLE_AZURE_AUTH_SOURCE) environment variable.
            - When set to C(msi), the host machine must be an azure resource with an enabled MSI extension. C(subscription_id) or the
              environment variable C(AZURE_SUBSCRIPTION_ID) can be used to identify the subscription ID if the resource is granted
              access to more than one subscription, otherwise the first subscription is chosen.
            - The C(msi) was added in Ansible 2.6.
        choices:
        - auto
        - cli
        - credential_file
        - env
        - msi
        default: auto
        version_added: 2.5
    api_profile:
        description:
        - Selects an API profile to use when communicating with Azure services. Default value of C(latest) is appropriate for public clouds;
          future values will allow use with Azure Stack.
        default: latest
        version_added: 2.5
requirements:
    - "python >= 2.7"
    - "azure >= 2.0.0"

notes:
    - For authentication with Azure you can pass parameters, set environment variables or use a profile stored
      in ~/.azure/credentials. Authentication is possible using a service principal or Active Directory user.
      To authenticate via service principal, pass subscription_id, client_id, secret and tenant or set environment
      variables AZURE_SUBSCRIPTION_ID, AZURE_CLIENT_ID, AZURE_SECRET and AZURE_TENANT.
    - To authenticate via Active Directory user, pass ad_user and password, or set AZURE_AD_USER and
      AZURE_PASSWORD in the environment.
    - "Alternatively, credentials can be stored in ~/.azure/credentials. This is an ini file containing
      a [default] section and the following keys: subscription_id, client_id, secret and tenant or
      subscription_id, ad_user and password. It is also possible to add additional profiles. Specify the profile
      by passing profile or setting AZURE_PROFILE in the environment."
    '''

#!/usr/bin/env python
#
# This script borrows a great deal of code from the azure_rm.py dynamic inventory script
# that is packaged with Ansible.  This can be found in the Ansible GitHub project at:
# https://github.com/ansible/ansible/blob/devel/contrib/inventory/azure_rm.py
#
# The Azure Dynamic Inventory script was written by:
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
# Altered/Added for Vault functionality:
#                    Austin Hobbs, GitHub: @OxHobbs

'''
Ansible Vault Password with Azure Key Vault Secret Script
=========================================================
This script is designed to be used with Ansible Vault.  It provides the
capability to provide this script as the password file to the ansible-vault
command.  This script uses the Azure Python SDK. For instruction on installing
the Azure Python SDK see http://azure-sdk-for-python.readthedocs.org/

Authentication
--------------
The order of precedence is command line arguments, environment variables,
and finally the [default] profile found in ~/.azure/credentials for all
authentication parameters.

If using a credentials file, it should be an ini formatted file with one or
more sections, which we refer to as profiles. The script looks for a
[default] section, if a profile is not specified either on the command line
or with an environment variable. The keys in a profile will match the
list of command line arguments below.

For command line arguments and environment variables specify a profile found
in your ~/.azure/credentials file, or a service principal or Active Directory
user.

Command line arguments:
 - profile
 - client_id
 - secret
 - subscription_id
 - tenant
 - ad_user
 - password
 - cloud_environment
 - adfs_authority_url
 - vault-name
 - secret-name
 - secret-version

Environment variables:
 - AZURE_PROFILE
 - AZURE_CLIENT_ID
 - AZURE_SECRET
 - AZURE_SUBSCRIPTION_ID
 - AZURE_TENANT
 - AZURE_AD_USER
 - AZURE_PASSWORD
 - AZURE_CLOUD_ENVIRONMENT
 - AZURE_ADFS_AUTHORITY_URL
 - AZURE_VAULT_NAME
 - AZURE_VAULT_SECRET_NAME
 - AZURE_VAULT_SECRET_VERSION


Vault
-----

The order of precedence of Azure Key Vault Secret information is the same.
Command line arguments, environment variables, and finally the azure_vault.ini
file with the [azure_keyvault] section.

azure_vault.ini (or azure_rm.ini if merged with Azure Dynamic Inventory Script)
------------------------------------------------------------------------------
As mentioned above, you can control execution using environment variables or a .ini file. A sample
azure_vault.ini is included. The name of the .ini file is the basename of the inventory script (in this case
'azure_vault') with a .ini extension. It also assumes the .ini file is alongside the script. To specify
a different path for the .ini file, define the AZURE_VAULT_INI_PATH environment variable:

  export AZURE_VAULT_INI_PATH=/path/to/custom.ini
  or
  export AZURE_VAULT_INI_PATH=[same path as azure_rm.ini if merged]

  __NOTE__: If using the azure_rm.py dynamic inventory script, it is possible to use the same .ini
  file for both the azure_rm dynamic inventory and the azure_vault password file.  Simply add a section
  named [azure_keyvault] to the ini file with the following properties: vault_name, secret_name and
  secret_version.

Examples:
---------
  Validate the vault_pw script with Python
  $ python azure_vault.py -n mydjangovault -s vaultpw -v 6b6w7f7252b44eac8ee726b3698009f3
  $ python azure_vault.py --vault-name 'mydjangovault' --secret-name 'vaultpw' \
    --secret-version 6b6w7f7252b44eac8ee726b3698009f3

  Use with a playbook
  $ ansible-playbook -i ./azure_rm.py my_playbook.yml --limit galaxy-qa --vault-password-file ./azure_vault.py


Insecure Platform Warning
-------------------------
If you receive InsecurePlatformWarning from urllib3, install the
requests security packages:

    pip install requests[security]


author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)
    - Austin Hobbs (@OxHobbs)

Company: Ansible by Red Hat, Microsoft

Version: 0.1.0
'''

import argparse
import os
import re
import sys
import inspect
from azure.keyvault import KeyVaultClient

from ansible.module_utils.six.moves import configparser as cp

from os.path import expanduser
import ansible.module_utils.six.moves.urllib.parse as urlparse

HAS_AZURE = True
HAS_AZURE_EXC = None
HAS_AZURE_CLI_CORE = True
CLIError = None

try:
    from msrestazure.azure_active_directory import AADTokenCredentials
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_active_directory import MSIAuthentication
    from msrestazure import azure_cloud
    from azure.mgmt.compute import __version__ as azure_compute_version
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
    from azure.common.credentials import ServicePrincipalCredentials, UserPassCredentials
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.subscriptions import SubscriptionClient
    from azure.mgmt.compute import ComputeManagementClient
    from adal.authentication_context import AuthenticationContext
except ImportError as exc:
    HAS_AZURE_EXC = exc
    HAS_AZURE = False

try:
    from azure.cli.core.util import CLIError
    from azure.common.credentials import get_azure_cli_credentials, get_cli_profile
    from azure.common.cloud import get_cli_active_cloud
except ImportError:
    HAS_AZURE_CLI_CORE = False
    CLIError = Exception

try:
    from ansible.release import __version__ as ansible_version
except ImportError:
    ansible_version = 'unknown'


AZURE_CREDENTIAL_ENV_MAPPING = dict(
    profile='AZURE_PROFILE',
    subscription_id='AZURE_SUBSCRIPTION_ID',
    client_id='AZURE_CLIENT_ID',
    secret='AZURE_SECRET',
    tenant='AZURE_TENANT',
    ad_user='AZURE_AD_USER',
    password='AZURE_PASSWORD',
    cloud_environment='AZURE_CLOUD_ENVIRONMENT',
    adfs_authority_url='AZURE_ADFS_AUTHORITY_URL'
)

AZURE_VAULT_SETTINGS = dict(
    vault_name='AZURE_VAULT_NAME',
    secret_name='AZURE_VAULT_SECRET_NAME',
    secret_version='AZURE_VAULT_SECRET_VERSION',
)

AZURE_MIN_VERSION = "2.0.0"
ANSIBLE_USER_AGENT = 'Ansible/{0}'.format(ansible_version)


class AzureRM(object):

    def __init__(self, args):
        self._args = args
        self._cloud_environment = None
        self._compute_client = None
        self._resource_client = None
        self._network_client = None
        self._adfs_authority_url = None
        self._vault_client = None
        self._resource = None

        self.debug = False
        if args.debug:
            self.debug = True

        self.credentials = self._get_credentials(args)
        if not self.credentials:
            self.fail("Failed to get credentials. Either pass as parameters, set environment variables, "
                      "or define a profile in ~/.azure/credentials.")

        # if cloud_environment specified, look up/build Cloud object
        raw_cloud_env = self.credentials.get('cloud_environment')
        if not raw_cloud_env:
            self._cloud_environment = azure_cloud.AZURE_PUBLIC_CLOUD  # SDK default
        else:
            # try to look up "well-known" values via the name attribute on azure_cloud members
            all_clouds = [x[1] for x in inspect.getmembers(azure_cloud) if isinstance(x[1], azure_cloud.Cloud)]
            matched_clouds = [x for x in all_clouds if x.name == raw_cloud_env]
            if len(matched_clouds) == 1:
                self._cloud_environment = matched_clouds[0]
            elif len(matched_clouds) > 1:
                self.fail("Azure SDK failure: more than one cloud matched for cloud_environment name '{0}'".format(
                    raw_cloud_env))
            else:
                if not urlparse.urlparse(raw_cloud_env).scheme:
                    self.fail("cloud_environment must be an endpoint discovery URL or one of {0}".format(
                        [x.name for x in all_clouds]))
                try:
                    self._cloud_environment = azure_cloud.get_cloud_from_metadata_endpoint(raw_cloud_env)
                except Exception as e:
                    self.fail("cloud_environment {0} could not be resolved: {1}".format(raw_cloud_env, e.message))

        if self.credentials.get('subscription_id', None) is None:
            self.fail("Credentials did not include a subscription_id value.")
        self.log("setting subscription_id")
        self.subscription_id = self.credentials['subscription_id']

        # get authentication authority
        # for adfs, user could pass in authority or not.
        # for others, use default authority from cloud environment
        if self.credentials.get('adfs_authority_url'):
            self._adfs_authority_url = self.credentials.get('adfs_authority_url')
        else:
            self._adfs_authority_url = self._cloud_environment.endpoints.active_directory

        # get resource from cloud environment
        self._resource = self._cloud_environment.endpoints.active_directory_resource_id

        if self.credentials.get('credentials'):
            self.azure_credentials = self.credentials.get('credentials')
        elif self.credentials.get('client_id') and self.credentials.get('secret') and self.credentials.get('tenant'):
            self.azure_credentials = ServicePrincipalCredentials(client_id=self.credentials['client_id'],
                                                                 secret=self.credentials['secret'],
                                                                 tenant=self.credentials['tenant'],
                                                                 cloud_environment=self._cloud_environment)

        elif self.credentials.get('ad_user') is not None and \
                self.credentials.get('password') is not None and \
                self.credentials.get('client_id') is not None and \
                self.credentials.get('tenant') is not None:

            self.azure_credentials = self.acquire_token_with_username_password(
                self._adfs_authority_url,
                self._resource,
                self.credentials['ad_user'],
                self.credentials['password'],
                self.credentials['client_id'],
                self.credentials['tenant'])

        elif self.credentials.get('ad_user') is not None and self.credentials.get('password') is not None:
            tenant = self.credentials.get('tenant')
            if not tenant:
                tenant = 'common'
            self.azure_credentials = UserPassCredentials(self.credentials['ad_user'],
                                                         self.credentials['password'],
                                                         tenant=tenant,
                                                         cloud_environment=self._cloud_environment)

        else:
            self.fail("Failed to authenticate with provided credentials. Some attributes were missing. "
                      "Credentials must include client_id, secret and tenant or ad_user and password, or "
                      "ad_user, password, client_id, tenant and adfs_authority_url(optional) for ADFS authentication, "
                      "or be logged in using AzureCLI.")

    def log(self, msg):
        if self.debug:
            print(msg + u'\n')

    def fail(self, msg):
        raise Exception(msg)

    def _get_profile(self, profile="default"):
        path = expanduser("~")
        path += "/.azure/credentials"
        try:
            config = cp.ConfigParser()
            config.read(path)
        except Exception as exc:
            self.fail("Failed to access {0}. Check that the file exists and you have read "
                      "access. {1}".format(path, str(exc)))
        credentials = dict()
        for key in AZURE_CREDENTIAL_ENV_MAPPING:
            try:
                credentials[key] = config.get(profile, key, raw=True)
            except Exception:
                pass

        if credentials.get('client_id') is not None or credentials.get('ad_user') is not None:
            return credentials

        return None

    def _get_env_credentials(self):
        env_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            env_credentials[attribute] = os.environ.get(env_variable, None)

        if env_credentials['profile'] is not None:
            credentials = self._get_profile(env_credentials['profile'])
            return credentials

        if env_credentials['client_id'] is not None or env_credentials['ad_user'] is not None:
            return env_credentials

        return None

    def _get_azure_cli_credentials(self):
        credentials, subscription_id = get_azure_cli_credentials()
        cloud_environment = get_cli_active_cloud()

        cli_credentials = {
            'credentials': credentials,
            'subscription_id': subscription_id,
            'cloud_environment': cloud_environment
        }
        return cli_credentials

    def _get_msi_credentials(self, subscription_id_param=None):
        credentials = MSIAuthentication()
        try:
            # try to get the subscription in MSI to test whether MSI is enabled
            subscription_client = SubscriptionClient(credentials)
            subscription = next(subscription_client.subscriptions.list())
            subscription_id = str(subscription.subscription_id)
            return {
                'credentials': credentials,
                'subscription_id': subscription_id_param or subscription_id
            }
        except Exception as exc:
            return None

    def _get_credentials(self, params):
        # Get authentication credentials.
        # Precedence: cmd line parameters-> environment variables-> default profile in ~/.azure/credentials.

        self.log('Getting credentials')

        arg_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            arg_credentials[attribute] = getattr(params, attribute)

        # try module params
        if arg_credentials['profile'] is not None:
            self.log('Retrieving credentials with profile parameter.')
            credentials = self._get_profile(arg_credentials['profile'])
            return credentials

        if arg_credentials['client_id'] is not None:
            self.log('Received credentials from parameters.')
            return arg_credentials

        if arg_credentials['ad_user'] is not None:
            self.log('Received credentials from parameters.')
            return arg_credentials

        # try environment
        env_credentials = self._get_env_credentials()
        if env_credentials:
            self.log('Received credentials from env.')
            return env_credentials

        # try default profile from ~./azure/credentials
        default_credentials = self._get_profile()
        if default_credentials:
            self.log('Retrieved default profile credentials from ~/.azure/credentials.')
            return default_credentials

        msi_credentials = self._get_msi_credentials(arg_credentials.get('subscription_id'))
        if msi_credentials:
            self.log('Retrieved credentials from MSI.')
            return msi_credentials

        try:
            if HAS_AZURE_CLI_CORE:
                self.log('Retrieving credentials from AzureCLI profile')
            cli_credentials = self._get_azure_cli_credentials()
            return cli_credentials
        except CLIError as ce:
            self.log('Error getting AzureCLI profile credentials - {0}'.format(ce))

        return None

    def acquire_token_with_username_password(self, authority, resource, username, password, client_id, tenant):
        authority_uri = authority

        if tenant is not None:
            authority_uri = authority + '/' + tenant

        context = AuthenticationContext(authority_uri)
        token_response = context.acquire_token_with_username_password(resource, username, password, client_id)
        return AADTokenCredentials(token_response)

    def _register(self, key):
        try:
            # We have to perform the one-time registration here. Otherwise, we receive an error the first
            # time we attempt to use the requested client.
            resource_client = self.rm_client
            resource_client.providers.register(key)
        except Exception as exc:
            self.log("One-time registration of {0} failed - {1}".format(key, str(exc)))
            self.log("You might need to register {0} using an admin account".format(key))
            self.log(("To register a provider using the Python CLI: "
                      "https://docs.microsoft.com/azure/azure-resource-manager/"
                      "resource-manager-common-deployment-errors#noregisteredproviderfound"))

    def get_mgmt_svc_client(self, client_type, base_url, api_version):
        client = client_type(self.azure_credentials,
                             self.subscription_id,
                             base_url=base_url,
                             api_version=api_version)
        client.config.add_user_agent(ANSIBLE_USER_AGENT)
        return client

    def get_vault_client(self):
        return KeyVaultClient(self.azure_credentials)

    def get_vault_suffix(self):
        return self._cloud_environment.suffixes.keyvault_dns

    @property
    def network_client(self):
        self.log('Getting network client')
        if not self._network_client:
            self._network_client = self.get_mgmt_svc_client(NetworkManagementClient,
                                                            self._cloud_environment.endpoints.resource_manager,
                                                            '2017-06-01')
            self._register('Microsoft.Network')
        return self._network_client

    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self._resource_client = self.get_mgmt_svc_client(ResourceManagementClient,
                                                             self._cloud_environment.endpoints.resource_manager,
                                                             '2017-05-10')
        return self._resource_client

    @property
    def compute_client(self):
        self.log('Getting compute client')
        if not self._compute_client:
            self._compute_client = self.get_mgmt_svc_client(ComputeManagementClient,
                                                            self._cloud_environment.endpoints.resource_manager,
                                                            '2017-03-30')
            self._register('Microsoft.Compute')
        return self._compute_client

    @property
    def vault_client(self):
        self.log('Getting the Key Vault client')
        if not self._vault_client:
            self._vault_client = self.get_vault_client()

        return self._vault_client


class AzureKeyVaultSecret:

    def __init__(self):

        self._args = self._parse_cli_args()

        try:
            rm = AzureRM(self._args)
        except Exception as e:
            sys.exit("{0}".format(str(e)))

        self._get_vault_settings()

        if self._args.vault_name:
            self.vault_name = self._args.vault_name

        if self._args.secret_name:
            self.secret_name = self._args.secret_name

        if self._args.secret_version:
            self.secret_version = self._args.secret_version

        self._vault_suffix = rm.get_vault_suffix()
        self._vault_client = rm.vault_client

        print(self.get_password_from_vault())

    def _parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description='Obtain the vault password used to secure your Ansilbe secrets'
        )
        parser.add_argument('-n', '--vault-name', action='store', help='Name of Azure Key Vault')
        parser.add_argument('-s', '--secret-name', action='store',
                            help='Name of the secret stored in Azure Key Vault')
        parser.add_argument('-v', '--secret-version', action='store',
                            help='Version of the secret to be retrieved')
        parser.add_argument('--debug', action='store_true', default=False,
                            help='Send the debug messages to STDOUT')
        parser.add_argument('--profile', action='store',
                            help='Azure profile contained in ~/.azure/credentials')
        parser.add_argument('--subscription_id', action='store',
                            help='Azure Subscription Id')
        parser.add_argument('--client_id', action='store',
                            help='Azure Client Id ')
        parser.add_argument('--secret', action='store',
                            help='Azure Client Secret')
        parser.add_argument('--tenant', action='store',
                            help='Azure Tenant Id')
        parser.add_argument('--ad_user', action='store',
                            help='Active Directory User')
        parser.add_argument('--password', action='store',
                            help='password')
        parser.add_argument('--adfs_authority_url', action='store',
                            help='Azure ADFS authority url')
        parser.add_argument('--cloud_environment', action='store',
                            help='Azure Cloud Environment name or metadata discovery URL')

        return parser.parse_args()

    def get_password_from_vault(self):
        vault_url = 'https://{0}{1}'.format(self.vault_name, self._vault_suffix)
        secret = self._vault_client.get_secret(vault_url, self.secret_name, self.secret_version)
        return secret.value

    def _get_vault_settings(self):
        env_settings = self._get_vault_env_settings()
        if None not in set(env_settings.values()):
            for key in AZURE_VAULT_SETTINGS:
                setattr(self, key, env_settings.get(key, None))
        else:
            file_settings = self._load_vault_settings()
            if not file_settings:
                return

            for key in AZURE_VAULT_SETTINGS:
                if file_settings.get(key):
                    setattr(self, key, file_settings.get(key))

    def _get_vault_env_settings(self):
        env_settings = dict()
        for attribute, env_variable in AZURE_VAULT_SETTINGS.items():
            env_settings[attribute] = os.environ.get(env_variable, None)
        return env_settings

    def _load_vault_settings(self):
        basename = os.path.splitext(os.path.basename(__file__))[0]
        default_path = os.path.join(os.path.dirname(__file__), (basename + '.ini'))
        path = os.path.expanduser(os.path.expandvars(os.environ.get('AZURE_VAULT_INI_PATH', default_path)))
        config = None
        settings = None
        try:
            config = cp.ConfigParser()
            config.read(path)
        except Exception:
            pass

        if config is not None:
            settings = dict()
            for key in AZURE_VAULT_SETTINGS:
                try:
                    settings[key] = config.get('azure_keyvault', key, raw=True)
                except Exception:
                    pass

        return settings


def main():
    if not HAS_AZURE:
        sys.exit("The Azure python sdk is not installed (try `pip install 'azure>={0}' --upgrade`) - {1}".format(
            AZURE_MIN_VERSION, HAS_AZURE_EXC))

    AzureKeyVaultSecret()


if __name__ == '__main__':
    main()

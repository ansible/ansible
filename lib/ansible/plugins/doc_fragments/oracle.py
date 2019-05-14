# Copyright (c) 2018, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    DOCUMENTATION = """
    requirements:
        - "python >= 2.7"
        -  Python SDK for Oracle Cloud Infrastructure U(https://oracle-cloud-infrastructure-python-sdk.readthedocs.io)
    notes:
        - For OCI python sdk configuration, please refer to
          U(https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/configuration.html)
    options:
        config_file_location:
            description:
                - Path to configuration file. If not set then the value of the OCI_CONFIG_FILE environment variable,
                  if any, is used. Otherwise, defaults to ~/.oci/config.
            type: str
        config_profile_name:
            description:
                - The profile to load from the config file referenced by C(config_file_location). If not set, then the
                  value of the OCI_CONFIG_PROFILE environment variable, if any, is used. Otherwise, defaults to the
                  "DEFAULT" profile in C(config_file_location).
            default: "DEFAULT"
            type: str
        api_user:
            description:
                - The OCID of the user, on whose behalf, OCI APIs are invoked. If not set, then the
                  value of the OCI_USER_OCID environment variable, if any, is used. This option is required if the user
                  is not specified through a configuration file (See C(config_file_location)). To get the user's OCID,
                  please refer U(https://docs.us-phoenix-1.oraclecloud.com/Content/API/Concepts/apisigningkey.htm).
            type: str
        api_user_fingerprint:
            description:
                - Fingerprint for the key pair being used. If not set, then the value of the OCI_USER_FINGERPRINT
                  environment variable, if any, is used. This option is required if the key fingerprint is not
                  specified through a configuration file (See C(config_file_location)). To get the key pair's
                  fingerprint value please refer
                  U(https://docs.us-phoenix-1.oraclecloud.com/Content/API/Concepts/apisigningkey.htm).
            type: str
        api_user_key_file:
            description:
                - Full path and filename of the private key (in PEM format). If not set, then the value of the
                  OCI_USER_KEY_FILE variable, if any, is used. This option is required if the private key is
                  not specified through a configuration file (See C(config_file_location)). If the key is encrypted
                  with a pass-phrase, the C(api_user_key_pass_phrase) option must also be provided.
            type: str
        api_user_key_pass_phrase:
            description:
                - Passphrase used by the key referenced in C(api_user_key_file), if it is encrypted. If not set, then
                  the value of the OCI_USER_KEY_PASS_PHRASE variable, if any, is used. This option is required if the
                  key passphrase is not specified through a configuration file (See C(config_file_location)).
            type: str
        auth_type:
            description:
                - The type of authentication to use for making API requests. By default C(auth_type="api_key") based
                  authentication is performed and the API key (see I(api_user_key_file)) in your config file will be
                  used. If this 'auth_type' module option is not specified, the value of the OCI_ANSIBLE_AUTH_TYPE,
                  if any, is used. Use C(auth_type="instance_principal") to use instance principal based authentication
                  when running ansible playbooks within an OCI compute instance.
            choices: ['api_key', 'instance_principal']
            default: 'api_key'
            type: str
        tenancy:
            description:
                - OCID of your tenancy. If not set, then the value of the OCI_TENANCY variable, if any, is
                  used. This option is required if the tenancy OCID is not specified through a configuration file
                  (See C(config_file_location)). To get the tenancy OCID, please refer
                  U(https://docs.us-phoenix-1.oraclecloud.com/Content/API/Concepts/apisigningkey.htm)
            type: str
        region:
            description:
                - The Oracle Cloud Infrastructure region to use for all OCI API requests. If not set, then the
                  value of the OCI_REGION variable, if any, is used. This option is required if the region is
                  not specified through a configuration file (See C(config_file_location)). Please refer to
                  U(https://docs.us-phoenix-1.oraclecloud.com/Content/General/Concepts/regions.htm) for more information
                  on OCI regions.
            type: str
    """

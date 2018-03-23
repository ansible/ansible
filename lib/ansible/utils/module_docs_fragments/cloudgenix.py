class ModuleDocFragment(object):
    # Cloudgenix documentation fragment
    DOCUMENTATION = """
options:
  auth_token:
    description:
      - CloudGenix API AUTH_TOKEN. If not set, then the value of the X_AUTH_TOKEN environment variable is used.
    required: false
    default: null
    aliases: [ 'x_auth_token' ]
  tenant_id:
    description:
      - Tenant ID to make requests on. If not set, the TENANT_ID environment variable is used if set, otherwise the ID
        is queried from the API using the auth_token.
    required: false
    default: null
  controller:
    description:
      - Controller API Endpoint URL to use.
    required: false
    default: "https://api.elcapitan.cloudgenix.com"
  ssl_verify:
    description:
      - Enable strict verification of CloudGenix API SSL Certificate
    required: false
    default: True
    type: bool
  ignore_region:
    description:
      - Disable automatic controller URL rewriting based on region detection/response. Implicitly use Controller API
        URL without modification.
    required: false
    default: False
    type: bool

notes:
  - For more information on using Ansible to manage the CloudGenix App Fabric, see U(https://support.cloudgenix.com)
    or U(https://developers.cloudgenix.com).
  - Requires the C(cloudgenix) python module on the host. Typically, this is done with C(pip install cloudgenix).

requirements:
  - cloudgenix >= 4.6.1b1
"""

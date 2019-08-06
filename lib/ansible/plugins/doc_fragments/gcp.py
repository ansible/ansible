# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # GCP doc fragment.
    DOCUMENTATION = r'''
options:
    project:
        description:
            - The Google Cloud Platform project to use.
        type: str
    auth_kind:
        description:
            - The type of credential used.
        type: str
        required: true
        choices: [ application, machineaccount, serviceaccount ]
    service_account_contents:
        description:
            - The contents of a Service Account JSON file, either in a dictionary or as a JSON string that represents it.
        type: jsonarg
    service_account_file:
        description:
            - The path of a Service Account JSON file if serviceaccount is selected as type.
        type: path
    service_account_email:
        description:
            - An optional service account email address if machineaccount is selected
              and the user does not wish to use the default email.
        type: str
    scopes:
        description:
            - Array of scopes to be used.
        type: list
    env_type:
        description:
            - Specifies which Ansible environment you're running this module within.
            - This should not be set unless you know what you're doing.
            - This only alters the User Agent string for any API requests.
        type: str
notes:
  - for authentication, you can set service_account_file using the
    c(gcp_service_account_file) env variable.
  - for authentication, you can set service_account_contents using the
    c(GCP_SERVICE_ACCOUNT_CONTENTS) env variable.
  - For authentication, you can set service_account_email using the
    C(GCP_SERVICE_ACCOUNT_EMAIL) env variable.
  - For authentication, you can set auth_kind using the C(GCP_AUTH_KIND) env
    variable.
  - For authentication, you can set scopes using the C(GCP_SCOPES) env variable.
  - Environment variables values will only be used if the playbook values are
    not set.
  - The I(service_account_email) and I(service_account_file) options are
    mutually exclusive.
'''

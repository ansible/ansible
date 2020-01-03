#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Jacob Henner <code@ventricle.us>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
module: iam_oidc_federation
version_added: "2.10"
short_description: Maintain IAM OpenID Connect (OIDC) federation configuration.
requirements:
  - boto3
description:
  - Provides a mechanism to manage AWS IAM OpenID Connect (OIDC) identity providers (create/update/delete metadata).
options:
  url:
    description:
      - The URL of the OIDC provider to manage.
    required: true
    type: str
    aliases:
      - name
  client_ids:
    description:
      - A list of client IDs (also known as audiences).
      - You can register multiple client IDs with the same provider. For example, you might have multiple applications that use the same OIDC provider. You
        cannot register more than 100 client IDs with a single IAM OIDC provider.
      - Required when I(state=present).
    type: list
    elements: str
    aliases:
      - audiences
  thumbprints:
    description:
      - A list of server certificate thumbprints for the OpenID Connect (OIDC) identity provider's server certificates.
      - Typically this list includes only one entry. However, IAM lets you have up to five thumbprints for an OIDC provider. This lets you maintain multiple
        thumbprints if the identity provider is rotating certificates.
      - The server certificate thumbprint is the hex-encoded SHA-1 hash value of the X.509 certificate used by the domain where the OpenID Connect provider
        makes its keys available. It is always a 40-character string.
      - Required when I(state=present).
    type: list
    elements: str
  state:
    description:
      - Whether to create or delete identity provider. If 'present' is specified it will attempt to update the identity provider matching the name field.
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - aws
  - ec2
author:
  - Jacob Henner (@JacobHenner)
notes:
  - This module was derived from M(iam_saml_federation).
"""

EXAMPLES = """
# Note: These examples do not set authentication details, see the AWS Guide for details.
# It is assumed that their matching environment variables are set.
# Creates a new IAM OIDC identity provider if not present, updates the provider if it exists.
- name: Create/update IAM OIDC IdP
  iam_oidc_federation:
    url: https://oidc.eks.us-east-1.amazonaws.com/id/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    thumbprints:
      - beaa37307e5f6d89a7f803982ccde2da50063438
    client_ids:
      - sts.amazonaws.com
# Removes IAM OIDC identity provider
- name: Remove IAM OIDC IdP
  iam_oidc_federation:
    url: https://oidc.eks.us-east-1.amazonaws.com/id/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    state: absent
"""

RETURN = """
oidc_provider:
  description: Details of the OIDC identity provider that was created/modified.
  type: complex
  returned: present
  contains:
    arn:
      description: The ARN of the identity provider.
      type: str
      returned: present
      sample: "arn:aws:iam::012345678912:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    url:
      description: The URL of the OIDC identity provider, with no scheme specified.
      type: str
      returned: present
      sample: "oidc.eks.us-east-1.amazonaws.com/id/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    client_id_list:
      description: The list of client ids (audiences) for this identity provider.
      type: list
      elements: str
      returned: present
      sample:
        - sts.amazonaws.com
    thumbprint_list:
      description: The list of thumbprints for this identity provider.
      type: list
      elements: str
      returned: present
      sample:
        - beaa37307e5f6d89a7f803982ccde2da50063438
        - df3ed25f0c89a9c41d99123ba3b5d2c2105f2439
    create_date:
      description: The date and time when the OIDC provider was created in ISO 8601 date-time format.
      type: str
      returned: present
      sample: "2017-02-08T04:36:28+00:00"
"""

try:
    import botocore.exceptions
except ImportError:
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict
from ansible.module_utils.six.moves.urllib.parse import urlparse


class OIDCProviderManager:
    """Handles OIDC Identity Provider configuration"""

    def __init__(self, module):
        self.module = module

        try:
            self.conn = module.client("iam")
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Unknown boto error")

    # use retry decorator for boto3 calls
    @AWSRetry.backoff(tries=3, delay=5)
    def _list_open_id_connect_providers(self):
        return self.conn.list_open_id_connect_providers()

    @AWSRetry.backoff(tries=3, delay=5)
    def _get_open_id_connect_provider(self, arn):
        return self.conn.get_open_id_connect_provider(OpenIDConnectProviderArn=arn)

    @AWSRetry.backoff(tries=3, delay=5)
    def _update_open_id_connect_provider_thumbprint(self, arn, thumbprint_list):
        return self.conn.update_open_id_connect_provider_thumbprint(
            OpenIDConnectProviderArn=arn, ThumbprintList=thumbprint_list
        )

    @AWSRetry.backoff(tries=3, delay=5)
    def _add_client_id_to_open_id_connect_provider(self, arn, client_id):
        return self.conn.add_client_id_to_open_id_connect_provider(
            OpenIDConnectProviderArn=arn, ClientID=client_id
        )

    @AWSRetry.backoff(tries=3, delay=5)
    def _remove_client_id_from_open_id_connect_provider(self, arn, client_id):
        return self.conn.remove_client_id_from_open_id_connect_provider(
            OpenIDConnectProviderArn=arn, ClientID=client_id
        )

    @AWSRetry.backoff(tries=3, delay=5)
    def _create_open_id_connect_provider(self, url, client_id_list, thumbprint_list):
        return self.conn.create_open_id_connect_provider(
            Url=url, ClientIDList=client_id_list, ThumbprintList=thumbprint_list
        )

    @AWSRetry.backoff(tries=3, delay=5)
    def _delete_open_id_connect_provider(self, arn):
        return self.conn.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)

    def _get_provider_arn(self, url):
        schemeless_url = "".join(urlparse(url)[1:])
        providers = self._list_open_id_connect_providers()
        for provider in providers["OpenIDConnectProviderList"]:
            provider_name = provider["Arn"].split("/", 1)[1]
            if provider_name == schemeless_url:
                return provider["Arn"]
        return None

    def create_or_update_oidc_provider(self, url, client_ids, thumbprints):
        res = {"changed": False}
        try:
            arn = self._get_provider_arn(url)
        except (
            botocore.exceptions.ValidationError,
            botocore.exceptions.ClientError,
        ) as e:
            self.module.fail_json_aws(
                e,
                msg="Could not get the ARN of the identity provider '{0}'".format(url),
            )
        # If the arn exists, check to see if the IdP config needs to be updated.
        if arn:
            try:
                resp = self._get_open_id_connect_provider(arn)
            except (
                botocore.exceptions.ValidationError,
                botocore.exceptions.ClientError,
            ) as e:
                self.module.fail_json_aws(
                    e, msg="Could not retrieve the identity provider '{0}'".format(url),
                )

            # Sets are used to ensure there are no ordering mismatches between
            # the AWS API's response and the user's specifications.
            desired_client_ids = set(client_ids)
            current_client_ids = set(resp["ClientIDList"])

            if set(thumbprints) != set(resp["ThumbprintList"]):
                res["changed"] = True
                if not self.module.check_mode:
                    try:
                        resp = self._update_open_id_connect_provider_thumbprint(
                            arn, thumbprints
                        )
                    except botocore.exceptions.ClientError as e:
                        self.module.fail_json_aws(
                            e,
                            msg="Could not update thumbprints for identity provider '{0}'".format(
                                url
                            ),
                        )

            if desired_client_ids != current_client_ids:
                res["changed"] = True
                client_ids_to_add = desired_client_ids - current_client_ids
                client_ids_to_remove = current_client_ids - desired_client_ids
                # We start with adds to make sure we don't remove all client_ids
                # before new ones are added.
                #
                # Adds/removals are interleaved to make sure the client_id limit
                # isn't reached by a bulk-add.
                if not self.module.check_mode:
                    while len(client_ids_to_add) != 0 or len(client_ids_to_remove) != 0:
                        if len(client_ids_to_add) != 0:
                            try:
                                self._add_client_id_to_open_id_connect_provider(
                                    arn, client_ids_to_add.pop()
                                )
                            except botocore.exceptions.ClientError as e:
                                self.module.fail_json_aws(
                                    e,
                                    msg="Could not add client_id to OIDC provider '{0}'".format(
                                        url
                                    ),
                                )
                        if len(client_ids_to_remove) != 0:
                            try:
                                self._remove_client_id_from_open_id_connect_provider(
                                    arn, client_ids_to_remove.pop()
                                )
                            except botocore.exceptions.ClientError as e:
                                self.module.fail_json_aws(
                                    e,
                                    msg="Could not remove client_id from OIDC provider '{0}'".format(
                                        url
                                    ),
                                )
            res["oidc_provider"] = self._build_res(arn)

        # The IdP does not exist; create it.
        else:
            res["changed"] = True
            if not self.module.check_mode:
                try:
                    resp = self._create_open_id_connect_provider(
                        url, client_ids, thumbprints
                    )
                    res["oidc_provider"] = self._build_res(
                        resp["OpenIDConnectProviderArn"]
                    )
                except botocore.exceptions.ClientError as e:
                    self.module.fail_json_aws(
                        e,
                        msg="Could not create the OIDC identity provider '{0}'".format(
                            url
                        ),
                    )

        self.module.exit_json(**res)

    def delete_oidc_provider(self, url):
        res = {"changed": False}
        try:
            arn = self._get_provider_arn(url)
        except (
            botocore.exceptions.ValidationError,
            botocore.exceptions.ClientError,
        ) as e:
            self.module.fail_json_aws(
                e,
                msg="Could not get the ARN of the OIDC identity provider '{0}'".format(
                    url
                ),
            )

        # If OIDC provider exists; delete it.
        if arn:
            res["changed"] = True
            if not self.module.check_mode:
                try:
                    self._delete_open_id_connect_provider(arn)
                except botocore.exceptions.ClientError as e:
                    self.module.fail_json_aws(
                        e,
                        msg="Could not delete the OIDC identity provider '{0}'".format(
                            url
                        ),
                    )

        self.module.exit_json(**res)

    def _build_res(self, arn):
        oidc_provider = self._get_open_id_connect_provider(arn)
        return {
            "arn": arn,
            "url": oidc_provider["Url"],
            "client_id_list": oidc_provider["ClientIDList"],
            "thumbprint_list": oidc_provider["ThumbprintList"],
            "create_date": oidc_provider["CreateDate"].isoformat(),
        }


def main():
    argument_spec = dict(
        url=dict(required=True, aliases=["name"]),
        client_ids=dict(
            required=False, type="list", elements="str", aliases=["audiences"],
        ),
        thumbprints=dict(required=False, type="list", elements="str"),
        state=dict(default="present", choices=["present", "absent"],),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["client_ids", "thumbprints"])],
    )

    name = module.params["url"]
    state = module.params.get("state")
    client_ids = module.params.get("client_ids")
    thumbprints = module.params.get("thumbprints")

    oidc_manager = OIDCProviderManager(module)

    if state == "present":
        oidc_manager.create_or_update_oidc_provider(name, client_ids, thumbprints)
    elif state == "absent":
        oidc_manager.delete_oidc_provider(name)


if __name__ == "__main__":
    main()

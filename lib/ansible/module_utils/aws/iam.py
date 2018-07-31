# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback

try:
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    pass  # caught by HAS_BOTO3

from ansible.module_utils._text import to_native


def get_aws_account_id(module):
    """ Given AnsibleAWSModule instance, get the active AWS account ID

    get_account_id tries too find out the account that we are working
    on.  It's not guaranteed that this will be easy so we try in
    several different ways.  Giving either IAM or STS privilages to
    the account should be enough to permit this.
    """
    account_id = None
    try:
        sts_client = module.client('sts')
        account_id = sts_client.get_caller_identity().get('Account')
    # non-STS sessions may also get NoCredentialsError from this STS call, so
    # we must catch that too and try the IAM version
    except (ClientError, NoCredentialsError):
        try:
            iam_client = module.client('iam')
            account_id = iam_client.get_user()['User']['Arn'].split(':')[4]
        except ClientError as e:
            if (e.response['Error']['Code'] == 'AccessDenied'):
                except_msg = to_native(e)
                # don't match on `arn:aws` because of China region `arn:aws-cn` and similar
                account_id = except_msg.search(r"arn:\w+:iam::([0-9]{12,32}):\w+/").group(1)
            if account_id is None:
                module.fail_json_aws(e, msg="Could not get AWS account information")
        except Exception as e:
            module.fail_json(
                msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
                exception=traceback.format_exc()
            )
    if not account_id:
        module.fail_json(msg="Failed while determining AWS account ID. Try allowing sts:GetCallerIdentity or iam:GetUser permissions.")
    return to_native(account_id)

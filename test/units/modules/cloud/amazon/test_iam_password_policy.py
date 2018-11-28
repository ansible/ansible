import pytest

from units.modules.utils import set_module_args
from ansible.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("iam_password_policy.py requires the `boto3` and `botocore` modules")
else:
    import boto3
    from ansible.modules.cloud.amazon import iam_password_policy


def test_warn_if_state_not_specified():
    set_module_args({
        "min_pw_length": "8",
        "require_symbols": "false",
        "require_numbers": "true",
        "require_uppercase": "true",
        "require_lowercase": "true",
        "allow_pw_change": "true",
        "pw_max_age": "60",
        "pw_reuse_prevent": "5",
        "pw_expire": "false"
    })
    with pytest.raises(SystemExit):
        print(iam_password_policy.main())

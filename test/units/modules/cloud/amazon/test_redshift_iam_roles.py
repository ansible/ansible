
import boto3
import pytest

from units.modules.utils import set_module_args
from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.modules.cloud.amazon import redshift_iam_roles

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_redshift_role.py requires the `boto3` and `botocore` modules")

def test_warn_if_cluster_not_specified():
    set_module_args({
        "state": "present",
        "roles": [
            "arn:aws:iam::123456789012:role/superuser"
        ],
    })
    with pytest.raises(SystemExit):
        print(redshift_iam_roles.main())

def test_warn_if_state_not_specified():
    set_module_args({
        "cluster": "foobaz",
        "roles": [
            "arn:aws:iam::123456789012:role/superuser"
        ],
    })
    with pytest.raises(SystemExit):
        print(redshift_iam_roles.main())

def test_warn_if_roles_not_specified_during_add():
    set_module_args({
        "cluster": "foobaz",
        "state": "present"
    })
    with pytest.raises(SystemExit):
        print(redshift_iam_roles.main())

def test_warn_if_state_not_valid():
    set_module_args({
        "cluster": "foobaz",
        "state": "boofaz",
        "roles": [
            "arn:aws:iam::123456789012:role/superuser"
        ],
    })
    with pytest.raises(SystemExit):
        print(redshift_iam_roles.main())

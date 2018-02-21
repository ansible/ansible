import boto3
import pytest

from units.modules.utils import set_module_args
from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.modules.cloud.amazon import emr_add_steps

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("emr_add_steps.py requires the `boto3` and `botocore` modules")


def test_warn_if_cluster_id_not_specified():
    set_module_args({
        "steps": [{"name": "arbitrary_step"}]
    })
    with pytest.raises(SystemExit):
        print(emr_add_steps.main())

def test_warn_if_steps_not_specified():
    set_module_args({
        "cluster_id": "j-AZ1R45HYKET3"
    })
    with pytest.raises(SystemExit):
        print(emr_add_steps.main())

# AWS SSM Integration Test Setup

## aws_ssm_integration_test_setup_teardown

An Ansible role was created to perform integration test across aws_ssm connection plugin. The role performs the following actions.

- Create AWS Resources in user specified region.
- Perform integration Test across aws_ssm connection plugin.
- TearDown/Remove AWS Resources that are created for testing plugin.

### Prerequisites

- Make sure the machine used for testing already has Ansible repo with ssm connection plugin.
- AWS CLI/IAM-Role configured to the machine which has permissions to spin-up AWS resources.

### Variables referred in Ansible Role

The following table provide details about variables referred within Ansible Role.

| Variable Name | Details |
| ------ | ------ |
| aws_region | Name of AWS-region |
| iam_role_name | Name of IAM Role which will be attached to newly-created EC2-Instance |
| iam_policy_name | Name of IAM Policy which will be attached to the IAM role referred above |
| instance_type | Instance type user for creating EC2-Instance |
| instance_id | AWS EC2 Instance-Id (This gets populated by role) |
| bucket_name | Name of S3 buckted used by SSM (This gets populated by role) |

### Example Playbook

A sample example to demonstrate the usage of role within Ansible-playbook.(Make sure the respective variables are passed as parameters.)

```yaml
   - hosts: localhost
     roles:
       - aws_ssm_integration_test_setup_teardown
```

#### Author's Information

Krishna Nand Choudhary (krishnanandchoudhary)
Nikhil Araga (araganik)
Gaurav Ashtikar (gau1991)

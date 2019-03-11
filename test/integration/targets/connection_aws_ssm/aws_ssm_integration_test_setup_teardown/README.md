aws_ssm_integration_test_setup_teardown
=========

This role will create infrastructure for aws_ssm connection plugin, after integration test will get completed it will tear down infrastructure.

Requirements
------------

Ansible machine shoould AWS permission for all the resources used for aws_ssm connection plugin intrgration testing.

Role Variables
--------------

instance_type: Instace type which will created for testing
ami_id: AMI Id for the instance
iam_role_name: IAM role name, which will be atteched to the instance
iam_policy_name: IAM policy name, which is will be atteched to the role
region_name: AWS region id for resource creation
instance_id: It will created after EC2 instance is created.
bucket_name: Bucket name will be based on instance ID.


Example Playbook
----------------

Example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

   - hosts: localhost
     roles:
       - aws_ssm_integration_test_setup_teardown


Author Information
------------------

krishna nand choudhary
Nikhil Araga

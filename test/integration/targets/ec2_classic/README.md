# EC2 Classic tests can only be run on a pre-2013 AWS account with supported-platforms=EC2
Ansible CI does NOT have classic EC2 support; these tests are provided as-is for the 
community and can be run if you have access to a classic account.  To check if your account
has support for EC2 Classic you can use the `aws_account_attribute` plugin:
```
  vars:
    has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
```

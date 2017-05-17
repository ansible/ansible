This directory contains definitions to prepare an AWS account for running
Ansible tests.

   testing-iam-policy.json.j2

the testing-iam-policy.json.j2 file contains a policy which can be given to
the user running the tests to minimise the rights of that user.  Please note
that this does not fully restrict the user;  The user has wide privileges
for viewing account definitions and is also able to manage some resources
that are not related to testing (e.g. AWS lambdas with different names)
primarily due to the limitations of the Amazon ARN notation.  At the very
least the policy limits the user to one region, however tests should not
be run in a primary production account.

Apart from installing the policy and giving it to the user identity running
the tests, a lambda role `ansible_integration_tests` has to be created which
has lambda basic execution privileges.

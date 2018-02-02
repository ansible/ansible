# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # inventory cache
    DOCUMENTATION = """
options:
  aws_profile:
    description: The AWS profile
    aliases: ['boto_profile']
    env:
      - name: AWS_PROFILE
      - name: AWS_DEFAULT_PROFILE
  aws_access_key:
    description: The AWS access key to use.
    env:
      - name: AWS_ACCESS_KEY_ID
      - name: AWS_ACCESS_KEY
      - name: EC2_ACCESS_KEY
  aws_secret_key:
    description: The AWS secret key that corresponds to the access key.
    env:
      - name: AWS_SECRET_ACCESS_KEY
      - name: AWS_SECRET_KEY
      - name: EC2_SECRET_KEY
  aws_security_token:
    description: The AWS security token if using temporary access and secret keys.
    env:
      - name: AWS_SECURITY_TOKEN
      - name: AWS_SESSION_TOKEN
      - name: EC2_SECURITY_TOKEN
  region:
    description: The region for which to create the connection.
    env:
      - name: AWS_REGION
      - name: EC2_REGION
"""

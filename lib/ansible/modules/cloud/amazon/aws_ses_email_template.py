#!/usr/bin/python

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_ses_email_template
short_description: Manage an AWS SES email template
description:
    - Manage an AWS SES email template. See
      U(https://aws.amazon.com/blogs/messaging-and-targeting/introducing-email-templates-and-bulk-sending/) for details.
version_added: "2.7"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  template_name:
    description:
      - The name of the template. You will refer to this name when you send email using the SendTemplatedEmail or SendBulkTemplatedEmail operations.
    required: true
  subject_part:
    description:
      - The subject line of the email.
    required: false
  text_part:
    description:
      - The email body that will be visible to recipients whose email clients do not display HTML.
    required: false
  html_part:
    description:
      - The HTML body of the email.
    required: false
  state:
    description:
      - Create or delete the AWS SES email template.
    required: true
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
notes:
  - Amazon SES email templates use a jinja syntax for templating. Be careful to ensure strings are
    properly escaped.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an SES email template
- aws_ses_email_template:
    template_name: my_email_template
    subject_part: "{% raw %}Greetings, {{ name }}!{% endraw %}"
    text_part: "{% raw %}Dear {{ name }},\r\nYour favorite animal is {{ favoriteanimal }}.{% endraw %}"
    html_part: "{% raw %}<h1>Hello {{ name }}</h1><p>Your favorite animal is {{ favoriteanimal }}.</p>{% endraw %}"
    state: present

# Delete an SES email template
- aws_ses_email_template:
    template_name: my_email_template
    state: absent

'''

RETURN = '''
template_name:
    description: The name of the template. You will refer to this name when you send email using the
                 SendTemplatedEmail or SendBulkTemplatedEmail operations.
    returned: when state is present
    type: string
    sample: 10
subject_part:
    description: The subject line of the email.
    returned: when state is present
    type: string
text_part:
    description: The email body that will be visible to recipients whose email clients do not display HTML.
    returned: when state is present
    type: string
    sample: "Dear {{ name }},\r\nYour favorite animal is {{ favoriteanimal }}."
html_part:
    description: The HTML body of the email.
    returned: when state is present
    type: string
    sample: "<h1>Hello {{ name }}</h1><p>Your favorite animal is {{ favoriteanimal }}.</p>"
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _get_ses_email_template(connection, module, template_name):
    """
    Get an AWS SES email template based on name. If not found, return None.

    :param connection: AWS boto3 ses connection
    :param module: Ansible module
    :param template_name: Name of SES email template to get
    :return: boto3 AWS SES email template dict or None if not found
    """

    try:
        return connection.get_template(TemplateName=template_name)['Template']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'TemplateDoesNotExist':
            return None
        else:
            module.fail_json_aws(e)


def _compare_email_template_params(user_params, current_params):
    """
    Compare email template params. If there is a difference, return True immediately else return False

    :param user_params: the email template parameters passed by the user
    :param current_params: the email template parameters currently configured
    :return: True if any parameter is mismatched else False
    """

    # boto3 doesn't return some keys if the value is empty
    # To counter this, add the key if it's missing with a blank value

    user_params = user_params['Template']

    if 'TextPart' not in current_params:
        current_params['TextPart'] = ""
    if 'HtmlPart' not in current_params:
        current_params['HtmlPart'] = ""

    if 'SubjectPart' in user_params and user_params['SubjectPart'] != current_params['SubjectPart']:
        return True
    if 'TextPart' in user_params and user_params['TextPart'] != current_params['TextPart']:
        return True
    if 'HtmlPart' in user_params and user_params['HtmlPart'] != current_params['HtmlPart']:
        return True

    return False


def create_or_update_ses_email_template(connection, module, ses_template):
    """
    Create or update an AWS SES email template

    :param connection: AWS boto3 ses connection
    :param module: Ansible module
    :param ses_template: a dict of AWS SES email template parameters or None
    :return:
    """

    changed = False
    params = dict(Template=dict())
    params['Template']['TemplateName'] = module.params.get("template_name")
    if module.params.get("subject_part") is not None:
        params['Template']['SubjectPart'] = module.params.get("subject_part")
    if module.params.get("text_part") is not None:
        params['Template']['TextPart'] = module.params.get("text_part")
    if module.params.get("html_part") is not None:
        params['Template']['HtmlPart'] = module.params.get("html_part")

    # If ses_template is not None then check if it needs to be modified, else create it
    if ses_template:
        if _compare_email_template_params(params, ses_template):
            connection.update_template(**params)
            changed = True
    else:
        try:
            connection.create_template(**params)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    template = _get_ses_email_template(connection, module, params['Template']['TemplateName'])

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(template))


def delete_ses_email_template(connection, module, ses_template):
    """
    Delete an AWS SES email template

    :param connection: AWS boto3 ses connection
    :param module: Ansible module
    :param template_name: a dict of AWS SES email template parameters or None
    :return:
    """

    changed = False

    if ses_template:
        try:
            connection.delete_template(TemplateName=ses_template['TemplateName'])
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed)


def main():

    argument_spec = (
        dict(
            template_name=dict(type='str', required=True),
            subject_part=dict(type='str'),
            text_part=dict(type='str'),
            html_part=dict(type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['subject_part'])
                              ])

    connection = module.client('ses')

    state = module.params.get("state")

    ses_email_template = _get_ses_email_template(connection, module, module.params.get("template_name"))

    if state == 'present':
        create_or_update_ses_email_template(connection, module, ses_email_template)
    else:
        delete_ses_email_template(connection, module, ses_email_template)

if __name__ == '__main__':
    main()

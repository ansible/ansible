#!/usr/bin/python
"""
create Autosupport module to enable, disable or modify
"""

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)
description:
  - "Enable/Disable Autosupport"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_autosupport
options:
  state:
    description:
      - Specifies whether the AutoSupport daemon is present or absent.
      - When this setting is absent, delivery of all AutoSupport messages is turned off.
    choices: ['present', 'absent']
    default: present
  node_name:
    description:
      - The name fo the filer that owns the AutoSupport Configuration.
    required: true
  transport:
    description:
      - The name of the transport protocol used to deliver AutoSupport messages
    choices: ['http', 'https', 'smtp']
  noteto:
    description:
      - Specifies up to five recipients of full AutoSupport e-mail messages.
  post_url:
    description:
      - The URL used to deliver AutoSupport messages via HTTP POST
  mail_hosts:
    description:
      - List of mail server(s) used to deliver AutoSupport messages via SMTP.
      - Both host names and IP addresses may be used as valid input.
  support:
    description:
      - Specifies whether AutoSupport notification to technical support is enabled.
    type: bool
  from_address:
    description:
      - specify the e-mail address from which the node sends AutoSupport messages
  partner_address:
    description:
      - specify up to five e-mail addresses to receive all AutoSupport messages including periodic messages.
      - This parameter is typically used for support partners.
  to:
    description:
      - specify up to five e-mail addresses to receive AutoSupport messages that are most relevant for your internal organization.
  proxy_url:
    description:
      - specify an HTTP or HTTPS proxy if the -transport parameter is set to HTTP or HTTPS and your organization uses a proxy
  hostname_subject:
    description:
      - Specify whether the hostname of the node is included in the subject line of the AutoSupport message.
    type: bool
short_description: "NetApp ONTAP manage Autosupport"
version_added: "2.7"

"""

EXAMPLES = """
   - name: Enable autosupport
     na_ontap_autosupport:
       hostname: "{{ hostname }}"
       username: "{{ username }}"
       password: "{{ password }}"
       state: present
       node_name: test
       transport: https
       noteto: abc@def.com,def@ghi.com
       mail_hosts: 1.2.3.4,5.6.7.8
       support: False
       post_url: url/1.0/post

   - name: Disable autosupport
     na_ontap_autosupport:
       hostname: "{{ hostname }}"
       username: "{{ username }}"
       password: "{{ password }}"
       state: absent
       node_name: test

"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPasup(object):
    """Class with autosupport methods"""

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            node_name=dict(required=True, type='str'),
            transport=dict(required=False, type='str', choices=['smtp', 'http', 'https']),
            noteto=dict(required=False, type='list'),
            post_url=dict(reuired=False, type='str'),
            support=dict(required=False, type='bool'),
            mail_hosts=dict(required=False, type='list'),
            from_address=dict(required=False, type='str'),
            partner_address=dict(required=False, type='list'),
            to=dict(required=False, type='list'),
            proxy_url=dict(required=False, type='str'),
            hostname_subject=dict(required=False, type='bool'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # present or absent requires modifying state to enabled or disabled
        self.parameters['service_state'] = 'started' if self.parameters['state'] == 'present' else 'stopped'

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_autosupport_config(self):
        """
        Invoke zapi - get current autosupport status
        @return: 'true' or 'false' / FAILURE with an error_message
        """
        asup_details = netapp_utils.zapi.NaElement('autosupport-config-get')
        asup_details.add_new_child('node-name', self.parameters['node_name'])
        asup_info = dict()
        try:
            result = self.server.invoke_successfully(asup_details, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='%s' % to_native(error),
                                  exception=traceback.format_exc())
        # zapi invoke successful
        asup_attr_info = result.get_child_by_name('attributes').get_child_by_name('autosupport-config-info')
        current_state = asup_attr_info.get_child_content('is-enabled')
        if current_state == 'true':
            asup_info['service_state'] = 'started'
        elif current_state == 'false':
            asup_info['service_state'] = 'stopped'
        current_support = asup_attr_info.get_child_content('is-support-enabled')
        if current_support == 'true':
            asup_info['support'] = True
        elif current_support == 'false':
            asup_info['support'] = False
        hostname_subject = asup_attr_info.get_child_content('is-node-in-subject')
        if hostname_subject == 'true':
            asup_info['hostname_subject'] = True
        elif hostname_subject == 'false':
            asup_info['hostname_subject'] = False

        asup_info['transport'] = asup_attr_info.get_child_content('transport')
        asup_info['post_url'] = asup_attr_info.get_child_content('post-url')
        mail_hosts = asup_attr_info.get_child_by_name('mail-hosts')
        asup_info['from_address'] = asup_attr_info.get_child_content('from')
        asup_info['proxy_url'] = asup_attr_info.get_child_content('proxy-url')

        # mail hosts has one valid entry always
        if mail_hosts is not None:
            # get list of mail hosts
            asup_info['mail_hosts'] = [mail.get_content() for mail in mail_hosts.get_children()]
        email_list = asup_attr_info.get_child_by_name('noteto')
        # if email_list is empty, noteto is also empty
        asup_info['noteto'] = [] if email_list is None else [email.get_content() for email in email_list.get_children()]

        partner_email_list = asup_attr_info.get_child_by_name('partner-address')
        # if partner_email_list is empty, partner_address is also empty
        asup_info['partner_address'] = [] if partner_email_list is None else [email.get_content() for email in partner_email_list.get_children()]

        to_list = asup_attr_info.get_child_by_name('to')
        # if to_list is empty, to is also empty
        asup_info['to'] = [] if to_list is None else [email.get_content() for email in to_list.get_children()]

        return asup_info

    def modify_autosupport_config(self, modify):
        """
        Invoke zapi - modify autosupport config
        @return: NaElement object / FAILURE with an error_message
        """
        asup_details = netapp_utils.zapi.NaElement('autosupport-config-modify')
        asup_details.add_new_child('node-name', self.parameters['node_name'])
        if modify.get('service_state'):
            if modify.get('service_state') == 'started':
                asup_details.add_new_child('is-enabled', 'true')
            elif modify.get('service_state') == 'stopped':
                asup_details.add_new_child('is-enabled', 'false')
        if modify.get('support') is not None:
            if modify.get('support') is True:
                asup_details.add_new_child('is-support-enabled', 'true')
            elif modify.get('support') is False:
                asup_details.add_new_child('is-support-enabled', 'false')
        if modify.get('hostname_subject') is not None:
            if modify.get('hostname_subject') is True:
                asup_details.add_new_child('is-node-in-subject', 'true')
            elif modify.get('hostname_subject') is False:
                asup_details.add_new_child('is-node-in-subject', 'false')
        if modify.get('transport'):
            asup_details.add_new_child('transport', modify['transport'])
        if modify.get('post_url'):
            asup_details.add_new_child('post-url', modify['post_url'])
        if modify.get('from_address'):
            asup_details.add_new_child('from', modify['from_address'])
        if modify.get('proxy_url'):
            asup_details.add_new_child('proxy-url', modify['proxy_url'])
        if modify.get('noteto'):
            asup_email = netapp_utils.zapi.NaElement('noteto')
            asup_details.add_child_elem(asup_email)
            for email in modify.get('noteto'):
                asup_email.add_new_child('mail-address', email)
        if modify.get('partner_address'):
            asup_partner_address = netapp_utils.zapi.NaElement('partner-address')
            asup_details.add_child_elem(asup_partner_address)
            for email in modify.get('partner_address'):
                asup_partner_address.add_new_child('mail-address', email)
        if modify.get('to'):
            asup_to = netapp_utils.zapi.NaElement('to')
            asup_details.add_child_elem(asup_to)
            for email in modify.get('to'):
                asup_to.add_new_child('mail-address', email)
        if modify.get('mail_hosts'):
            asup_mail_hosts = netapp_utils.zapi.NaElement('mail-hosts')
            asup_details.add_child_elem(asup_mail_hosts)
            for mail in modify.get('mail_hosts'):
                asup_mail_hosts.add_new_child('string', mail)

        try:
            result = self.server.invoke_successfully(asup_details, enable_tunneling=True)
            return result
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='%s' % to_native(error),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to autosupport
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_autosupport", cserver)

        current = self.get_autosupport_config()
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if modify:
                    self.modify_autosupport_config(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    asup_obj = NetAppONTAPasup()
    asup_obj.apply()


if __name__ == '__main__':
    main()

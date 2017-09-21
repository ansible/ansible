# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
callback: mail
type: notification
short_description: Sends failure events via email
description:
- This callback will report failures via email
version_added: '2.0'
requirements:
- whitelisting in configuration
options:
  mta:
    description: Mail Transfer Agent, server that accepts SMTP
    env:
    - name: SMTPHOST
    default: localhost
note:
- "TODO: expand configuration options now that plugins can leverage Ansible's configuration"
'''

import json
import os
import re
import smtplib

from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    ''' This Ansible callback plugin mails errors to interested parties. '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mail'
    CALLBACK_NEEDS_WHITELIST = True

    def mail(self, subject='Ansible error mail', sender=None, to=None, cc=None, bcc=None, body=None, smtphost=None):
        if smtphost is None:
            smtphost = os.getenv('SMTPHOST', 'localhost')
        if sender is None:
            sender = '<root>'
        if to is None:
            to = 'root'
        if body is None:
            body = subject

        smtp = smtplib.SMTP(smtphost)

        b_sender = to_bytes(sender)
        b_to = to_bytes(to)
        b_cc = to_bytes(cc)
        b_bcc = to_bytes(bcc)
        b_subject = to_bytes(subject)
        b_body = to_bytes(body)

        b_content = b'From: %s\n' % b_sender
        b_content += b'To: %s\n' % b_to
        if cc:
            b_content += b'Cc: %s\n' % b_cc
        b_content += b'Subject: %s\n\n' % b_subject
        b_content += b_body

        b_addresses = b_to.split(b',')
        if cc:
            b_addresses += b_cc.split(b',')
        if bcc:
            b_addresses += b_bcc.split(b',')

        for b_address in b_addresses:
            smtp.sendmail(b_sender, b_address, b_content)

        smtp.quit()

    def subject_msg(self, multiline, failtype, linenr):
        return '%s: %s' % (failtype, multiline.strip('\r\n').splitlines()[linenr])

    def indent(self, multiline, indent=8):
        return re.sub('^', ' ' * indent, multiline, flags=re.MULTILINE)

    def body_blob(self, multiline, texttype):
        ''' Turn some text output in a well-indented block for sending in a mail body '''
        intro = 'with the following %s:\n\n' % texttype
        blob = ''
        for line in multiline.strip('\r\n').splitlines():
            blob += '%s\n' % line
        return intro + self.indent(blob) + '\n'

    def mail_result(self, result, failtype):
        host = result._host.get_name()
        sender = '"Ansible: %s" <root>' % host

        # Add subject
        if self.itembody:
            subject = self.itemsubject
        elif result._result.get('failed_when_result') is True:
            subject = "Failed due to 'failed_when' condition"
        elif result._result.get('exception'):
            subject = self.subject_msg(result._result['exception'], failtype, -1)
        elif result._result.get('msg'):
            subject = self.subject_msg(result._result['msg'], failtype, 0)
        elif result._result.get('stderr'):
            subject = self.subject_msg(result._result['stderr'], failtype, -1)
        elif result._result.get('stdout'):
            subject = self.subject_msg(result._result['stdout'], failtype, -1)
        else:
            subject = '%s: %s' % (failtype, result._task.name or result._task.action)

        # Make playbook name visible (e.g. in Outlook/Gmail condensed view)
        body = 'Playbook: %s\n' % os.path.basename(self.playbook._file_name)
        if result._task.name:
            body += 'Task: %s\n' % result._task.name
        body += 'Module: %s\n' % result._task.action
        body += 'Host: %s\n' % host
        body += '\n'

        # Add task information (as much as possible)
        body += 'The following task failed:\n\n'
        if 'invocation' in result._result:
            body += self.indent('%s: %s\n' % (result._task.action, json.dumps(result._result['invocation']['module_args'], indent=4)))
        elif result._task.name:
            body += self.indent('%s (%s)\n' % (result._task.name, result._task.action))
        else:
            body += self.indent('%s\n' % result._task.action)
        body += '\n'

        # Add item / message
        if self.itembody:
            body += self.itembody
        elif result._result.get('failed_when_result') is True:
            body += "due to the following condition:\n\n" + self.indent('failed_when:\n- ' + '\n- '.join(result._task.failed_when)) + '\n\n'
        elif result._result.get('msg'):
            body += self.body_blob(result._result['msg'], 'message')

        # Add stdout / stderr / exception / warnings / deprecations
        if result._result.get('exception'):
            body += self.body_blob(result._result['exception'], 'exception')
        if result._result.get('stdout'):
            body += self.body_blob(result._result['stdout'], 'standard output')
        if result._result.get('stderr'):
            body += self.body_blob(result._result['stderr'], 'error output')
        if result._result.get('warnings'):
            for i in range(len(result._result.get('warnings'))):
                body += self.body_blob(result._result['warnings'][i], 'exception %d' % i + 1)
        if result._result.get('deprecations'):
            for i in range(len(result._result.get('deprecations'))):
                body += self.body_blob(result._result['deprecations'][i], 'exception %d' % i + 1)

        body += 'and a complete dump of the error:\n\n'
        body += self.indent('%s: %s' % (failtype, json.dumps(result._result, indent=4)))

        self.mail(sender=sender, subject=subject, body=body)

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook
        self.itembody = ''

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            return

        self.mail_result(result, 'Failed')

    def v2_runner_on_unreachable(self, result):
        self.mail_result(result, 'Unreachable')

    def v2_runner_on_async_failed(self, result):
        self.mail_result(result, 'Async failure')

    def v2_runner_item_on_failed(self, result):
        # Pass item information to task failure
        self.itemsubject = result._result['msg']
        self.itembody += self.body_blob(json.dumps(result._result, indent=4), "failed item dump '%(item)s'" % result._result)
#        self.itembody += self.body_blob(json.dumps(dir(result), indent=4), "failed full dump '%(item)s'" % result._result)

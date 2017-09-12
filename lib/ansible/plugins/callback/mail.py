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
    version_added: "2.3"
    requirements:
      - whitelisting in configuration
      - logstash (python library)
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

    def body_blob(self, multiline, texttype):
        ''' Turn some text output in a well-indented block for sending in a mail body '''
        blob = 'with the following %s:\n\n' % texttype
        for line in multiline.strip('\r\n').splitlines():
            blob += '\t%s\n' % line
        return blob + '\n'

    def mail_result(self, result, failtype):
        host = result._host.get_name()

        sender = '"Ansible: %s" <root>' % host
        subject = '%s: %s' % (failtype, result._task.name or result._task.action)

        body = ''
        body += 'Playbook: %s\n' % os.path.basename(self.playbook._file_name)
        if result._task.name:
            body += 'Task: %s\n' % result._task.name
        body += 'Module: %s\n' % result._task.action
        body += 'Host: %s\n' % host
        body += '\n'

        body += 'The following task failed:\n\n'
        if 'invocation' in result._result:
            body += '\t%s: %s\n\n' % (result._task.action, json.dumps(result._result['invocation']['module_args']))
        elif result._task.name:
            body += '\t%s (%s)\n\n' % (result._task.name, result._task.action)
        else:
            body += '\t%s\n\n' % result._task.action

        if result._result.get('stdout'):
            subject = self.subject_msg(result._result['stdout'], failtype, -1)
            body += self.body_blob(result._result['stdout'], 'standard output')
        if result._result.get('stderr'):
            subject = self.subject_msg(result._result['stderr'], failtype, -1)
            body += self.body_blob(result._result['stderr'], 'error output')
        if result._result.get('msg'):
            subject = self.subject_msg(result._result['msg'], failtype, 0)
            body += self.body_blob(result._result['msg'], 'message')

        body += 'A complete dump of the error:\n\n'
        body += '\t%s: %s' % (failtype, json.dumps(result._result))

        self.mail(sender=sender, subject=subject, body=body)

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            return

        self.mail_result(result, 'Failed')

    def v2_runner_on_unreachable(self, result):
        self.mail_result(result, 'Unreachable')

    def v2_runner_on_async_failed(self, result):
        self.mail_result(result, 'Async failure')

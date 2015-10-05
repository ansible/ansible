#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
author: "Dag Wieers (@dagwieers)" 
module: mail
short_description: Send an email
description:
  - This module is useful for sending emails from playbooks.
  - One may wonder why automate sending emails?  In complex environments
    there are from time to time processes that cannot be automated, either
    because you lack the authority to make it so, or because not everyone
    agrees to a common approach.
  - If you cannot automate a specific step, but the step is non-blocking,
    sending out an email to the responsible party to make him perform his
    part of the bargain is an elegant way to put the responsibility in
    someone else's lap.
  - Of course sending out a mail can be equally useful as a way to notify
    one or more people in a team that a specific action has been
    (successfully) taken.
version_added: "0.8"
options:
  from:
    description:
      - The email-address the mail is sent from. May contain address and phrase.
    default: root
    required: false
  to:
    description:
      - The email-address(es) the mail is being sent to. This is
        a comma-separated list, which may contain address and phrase portions.
    default: root
    required: false
  cc:
    description:
      - The email-address(es) the mail is being copied to. This is
        a comma-separated list, which may contain address and phrase portions.
    required: false
  bcc:
    description:
      - The email-address(es) the mail is being 'blind' copied to. This is
        a comma-separated list, which may contain address and phrase portions.
    required: false
  subject:
    description:
      - The subject of the email being sent.
    required: true
  body:
    description:
      - The body of the email being sent.
    default: $subject
    required: false
  username:
    description:
      - If SMTP requires username
    default: null
    required: false
    version_added: "1.9"
  password:
    description:
      - If SMTP requires password
    default: null
    required: false
    version_added: "1.9"
  host:
    description:
      - The mail server
    default: 'localhost'
    required: false
  port:
    description:
      - The mail server port
    default: '25'
    required: false
    version_added: "1.0"
  attach:
    description:
      - A space-separated list of pathnames of files to attach to the message.
        Attached files will have their content-type set to C(application/octet-stream).
    default: null
    required: false
    version_added: "1.0"
  headers:
    description:
      - A vertical-bar-separated list of headers which should be added to the message.
        Each individual header is specified as C(header=value) (see example below).
    default: null
    required: false
    version_added: "1.0"
  charset:
    description:
      - The character set of email being sent
    default: 'us-ascii'
    required: false
  subtype:
    description:
      - The minor mime type, can be either text or html. The major type is always text.
    default: 'plain'
    required: false
    version_added: "2.0"
"""

EXAMPLES = '''
# Example playbook sending mail to root
- local_action: mail subject='System {{ ansible_hostname }} has been successfully provisioned.'

# Sending an e-mail using Gmail SMTP servers
- local_action: mail
                host='smtp.gmail.com'
                port=587
                username=username@gmail.com
                password='mysecret'
                to="John Smith <john.smith@example.com>"
                subject='Ansible-report'
                body='System {{ ansible_hostname }} has been successfully provisioned.'

# Send e-mail to a bunch of users, attaching files
- local_action: mail
                host='127.0.0.1'
                port=2025
                subject="Ansible-report"
                body="Hello, this is an e-mail. I hope you like it ;-)"
                from="jane@example.net (Jane Jolie)"
                to="John Doe <j.d@example.org>, Suzie Something <sue@example.com>"
                cc="Charlie Root <root@localhost>"
                attach="/etc/group /tmp/pavatar2.png"
                headers=Reply-To=john@example.com|X-Special="Something or other"
                charset=utf8
# Sending an e-mail using the remote machine, not the Ansible controller node
- mail:
    host='localhost'
    port=25
    to="John Smith <john.smith@example.com>"
    subject='Ansible-report'
    body='System {{ ansible_hostname }} has been successfully provisioned.'
'''

import os
import sys
import smtplib
import ssl

try:
    from email import encoders
    import email.utils
    from email.utils import parseaddr, formataddr
    from email.mime.base import MIMEBase
    from mail.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except ImportError:
    from email import Encoders as encoders
    import email.Utils
    from email.Utils import parseaddr, formataddr
    from email.MIMEBase import MIMEBase
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText

def main():

    module = AnsibleModule(
        argument_spec = dict(
            username = dict(default=None),
            password = dict(default=None),
            host = dict(default='localhost'),
            port = dict(default='25'),
            sender = dict(default='root', aliases=['from']),
            to = dict(default='root', aliases=['recipients']),
            cc = dict(default=None),
            bcc = dict(default=None),
            subject = dict(required=True, aliases=['msg']),
            body = dict(default=None),
            attach = dict(default=None),
            headers = dict(default=None),
            charset = dict(default='us-ascii'),
            subtype = dict(default='plain')
        )
    )

    username = module.params.get('username')
    password = module.params.get('password')
    host = module.params.get('host')
    port = module.params.get('port')
    sender = module.params.get('sender')
    recipients = module.params.get('to')
    copies = module.params.get('cc')
    blindcopies = module.params.get('bcc')
    subject = module.params.get('subject')
    body = module.params.get('body')
    attach_files = module.params.get('attach')
    headers = module.params.get('headers')
    charset = module.params.get('charset')
    subtype = module.params.get('subtype')
    sender_phrase, sender_addr = parseaddr(sender)

    if not body:
        body = subject

    try:
        try:
            smtp = smtplib.SMTP_SSL(host, port=int(port))
        except (smtplib.SMTPException, ssl.SSLError):
            smtp = smtplib.SMTP(host, port=int(port))
    except Exception, e:
        module.fail_json(rc=1, msg='Failed to send mail to server %s on port %s: %s' % (host, port, e))

    smtp.ehlo()
    if username and password:
        if smtp.has_extn('STARTTLS'):
            smtp.starttls()
        try:
            smtp.login(username, password)
        except smtplib.SMTPAuthenticationError:
            module.fail_json(msg="Authentication to %s:%s failed, please check your username and/or password" % (host, port))

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_phrase, sender_addr))
    msg.preamble = "Multipart message"

    if headers is not None:
        for hdr in [x.strip() for x in headers.split('|')]:
            try:
                h_key, h_val = hdr.split('=')
                msg.add_header(h_key, h_val)
            except:
                pass

    if 'X-Mailer' not in msg:
        msg.add_header('X-Mailer', "Ansible")

    to_list = []
    cc_list = []
    addr_list = []

    if recipients is not None:
        for addr in [x.strip() for x in recipients.split(',')]:
            to_list.append( formataddr( parseaddr(addr)) )
            addr_list.append( parseaddr(addr)[1] )    # address only, w/o phrase
    if copies is not None:
        for addr in [x.strip() for x in copies.split(',')]:
            cc_list.append( formataddr( parseaddr(addr)) )
            addr_list.append( parseaddr(addr)[1] )    # address only, w/o phrase
    if blindcopies is not None:
        for addr in [x.strip() for x in blindcopies.split(',')]:
            addr_list.append( parseaddr(addr)[1] )

    if len(to_list) > 0:
        msg['To'] = ", ".join(to_list)
    if len(cc_list) > 0:
        msg['Cc'] = ", ".join(cc_list)

    part = MIMEText(body + "\n\n", _subtype=subtype, _charset=charset)
    msg.attach(part)

    if attach_files is not None:
        for file in attach_files.split():
            try:
                fp = open(file, 'rb')

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(fp.read())
                fp.close()

                encoders.encode_base64(part)

                part.add_header('Content-disposition', 'attachment', filename=os.path.basename(file))
                msg.attach(part)
            except Exception, e:
                module.fail_json(rc=1, msg="Failed to send mail: can't attach file %s: %s" % (file, e))

    composed = msg.as_string()

    try:
        smtp.sendmail(sender_addr, set(addr_list), composed)
    except Exception, e:
        module.fail_json(rc=1, msg='Failed to send mail to %s: %s' % (", ".join(addr_list), e))

    smtp.quit()

    module.exit_json(changed=False)

# import module snippets
from ansible.module_utils.basic import *
main()

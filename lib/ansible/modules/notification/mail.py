#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- Dag Wieers (@dagwieers)
module: mail
short_description: Send an email
description:
- This module is useful for sending emails from playbooks.
- One may wonder why automate sending emails?  In complex environments
  there are from time to time processes that cannot be automated, either
  because you lack the authority to make it so, or because not everyone
  agrees to a common approach.
- If you cannot automate a specific step, but the step is non-blocking,
  sending out an email to the responsible party to make them perform their
  part of the bargain is an elegant way to put the responsibility in
  someone else's lap.
- Of course sending out a mail can be equally useful as a way to notify
  one or more people in a team that a specific action has been
  (successfully) taken.
version_added: '0.8'
options:
  from:
    description:
    - The email-address the mail is sent from. May contain address and phrase.
    default: root
  to:
    description:
    - The email-address(es) the mail is being sent to.
    - This is a list, which may contain address and phrase portions.
    default: root
    aliases: ['recipients']
  cc:
    description:
    - The email-address(es) the mail is being copied to.
    - This is a list, which may contain address and phrase portions.
  bcc:
    description:
    - The email-address(es) the mail is being 'blind' copied to.
    - This is a list, which may contain address and phrase portions.
  subject:
    description:
    - The subject of the email being sent.
    required: true
  body:
    description:
    - The body of the email being sent.
    default: $subject
  username:
    description:
    - If SMTP requires username.
    version_added: '1.9'
  password:
    description:
    - If SMTP requires password.
    version_added: '1.9'
  host:
    description:
    - The mail server.
    default: localhost
  port:
    description:
    - The mail server port.
    - This must be a valid integer between 1 and 65534
    default: 25
    version_added: '1.0'
  attach:
    description:
    - A list of pathnames of files to attach to the message.
    - Attached files will have their content-type set to C(application/octet-stream).
    default: []
    version_added: '1.0'
  headers:
    description:
    - A list of headers which should be added to the message.
    - Each individual header is specified as C(header=value) (see example below).
    default: []
    version_added: '1.0'
  charset:
    description:
    - The character set of email being sent.
    default: utf-8
  subtype:
    description:
    - The minor mime type, can be either C(plain) or C(html).
    - The major type is always C(text).
    choices: [ html, plain ]
    default: plain
    version_added: '2.0'
  secure:
    description:
    - If C(always), the connection will only send email if the connection is Encrypted.
      If the server doesn't accept the encrypted connection it will fail.
    - If C(try), the connection will attempt to setup a secure SSL/TLS session, before trying to send.
    - If C(never), the connection will not attempt to setup a secure SSL/TLS session, before sending
    - If C(starttls), the connection will try to upgrade to a secure SSL/TLS connection, before sending.
      If it is unable to do so it will fail.
    choices: [ always, never, starttls, try ]
    default: try
    version_added: '2.3'
  timeout:
    description:
    - Sets the timeout in seconds for connection attempts.
    default: 20
    version_added: '2.3'
'''

EXAMPLES = r'''
- name: Example playbook sending mail to root
  mail:
    subject: System {{ ansible_hostname }} has been successfully provisioned.
  delegate_to: localhost

- name: Sending an e-mail using Gmail SMTP servers
  mail:
    host: smtp.gmail.com
    port: 587
    username: username@gmail.com
    password: mysecret
    to: John Smith <john.smith@example.com>
    subject: Ansible-report
    body: System {{ ansible_hostname }} has been successfully provisioned.
  delegate_to: localhost

- name: Send e-mail to a bunch of users, attaching files
  mail:
    host: 127.0.0.1
    port: 2025
    subject: Ansible-report
    body: Hello, this is an e-mail. I hope you like it ;-)
    from: jane@example.net (Jane Jolie)
    to:
    - John Doe <j.d@example.org>
    - Suzie Something <sue@example.com>
    cc: Charlie Root <root@localhost>
    attach:
    - /etc/group
    - /tmp/avatar2.png
    headers:
    - Reply-To=john@example.com
    - X-Special="Something or other"
    charset: us-ascii
  delegate_to: localhost

- name: Sending an e-mail using the remote machine, not the Ansible controller node
  mail:
    host: localhost
    port: 25
    to: John Smith <john.smith@example.com>
    subject: Ansible-report
    body: System {{ ansible_hostname }} has been successfully provisioned.

- name: Sending an e-mail using Legacy SSL to the remote machine
  mail:
    host: localhost
    port: 25
    to: John Smith <john.smith@example.com>
    subject: Ansible-report
    body: System {{ ansible_hostname }} has been successfully provisioned.
    secure: always

- name: Sending an e-mail using StartTLS to the remote machine
  mail:
    host: localhost
    port: 25
    to: John Smith <john.smith@example.com>
    subject: Ansible-report
    body: System {{ ansible_hostname }} has been successfully provisioned.
    secure: starttls
'''

import os
import smtplib
import ssl
import traceback
from email import encoders
from email.utils import parseaddr, formataddr
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():

    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            host=dict(type='str', default='localhost'),
            port=dict(type='int', default=25),
            sender=dict(type='str', default='root', aliases=['from']),
            to=dict(type='list', default=['root'], aliases=['recipients']),
            cc=dict(type='list', default=[]),
            bcc=dict(type='list', default=[]),
            subject=dict(type='str', required=True, aliases=['msg']),
            body=dict(type='str'),
            attach=dict(type='list', default=[]),
            headers=dict(type='list', default=[]),
            charset=dict(type='str', default='utf-8'),
            subtype=dict(type='str', default='plain', choices=['html', 'plain']),
            secure=dict(type='str', default='try', choices=['always', 'never', 'starttls', 'try']),
            timeout=dict(type='int', default=20),
        ),
        required_together=[['password', 'username']],
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
    secure = module.params.get('secure')
    timeout = module.params.get('timeout')

    code = 0
    secure_state = False
    sender_phrase, sender_addr = parseaddr(sender)

    if not body:
        body = subject

    try:
        if secure != 'never':
            try:
                smtp = smtplib.SMTP_SSL(timeout=timeout)
                code, smtpmessage = smtp.connect(host, port=port)
                secure_state = True
            except ssl.SSLError as e:
                if secure == 'always':
                    module.fail_json(rc=1, msg='Unable to start an encrypted session to %s:%s: %s' %
                                               (host, port, to_native(e)), exception=traceback.format_exc())

        if not secure_state:
            smtp = smtplib.SMTP(timeout=timeout)
            code, smtpmessage = smtp.connect(host, port=port)

    except smtplib.SMTPException as e:
        module.fail_json(rc=1, msg='Unable to Connect %s:%s: %s' % (host, port, to_native(e)), exception=traceback.format_exc())

    try:
        smtp.ehlo()
    except smtplib.SMTPException as e:
            module.fail_json(rc=1, msg='Helo failed for host %s:%s: %s' % (host, port, to_native(e)), exception=traceback.format_exc())

    if int(code) > 0:
        if not secure_state and secure in ('starttls', 'try'):
            if smtp.has_extn('STARTTLS'):
                try:
                    smtp.starttls()
                    secure_state = True
                except smtplib.SMTPException as e:
                    module.fail_json(rc=1, msg='Unable to start an encrypted session to %s:%s: %s' %
                                     (host, port, to_native(e)), exception=traceback.format_exc())
                try:
                    smtp.ehlo()
                except smtplib.SMTPException as e:
                    module.fail_json(rc=1, msg='Helo failed for host %s:%s: %s' % (host, port, to_native(e)), exception=traceback.format_exc())
            else:
                if secure == 'starttls':
                    module.fail_json(rc=1, msg='StartTLS is not offered on server %s:%s' % (host, port))

    if username and password:
        if smtp.has_extn('AUTH'):
            try:
                smtp.login(username, password)
            except smtplib.SMTPAuthenticationError:
                module.fail_json(rc=1, msg='Authentication to %s:%s failed, please check your username and/or password' % (host, port))
            except smtplib.SMTPException:
                module.fail_json(rc=1, msg='No Suitable authentication method was found on %s:%s' % (host, port))
        else:
            module.fail_json(rc=1, msg="No Authentication on the server at %s:%s" % (host, port))

    if not secure_state and (username and password):
        module.warn('Username and Password was sent without encryption')

    msg = MIMEMultipart(_charset=charset)
    msg['From'] = formataddr((sender_phrase, sender_addr))
    msg['Subject'] = Header(subject, charset)
    msg.preamble = "Multipart message"

    for header in headers:
        # NOTE: Backward compatible with old syntax using '|' as delimiter
        for hdr in [x.strip() for x in header.split('|')]:
            try:
                h_key, h_val = hdr.split('=')
                h_val = to_native(Header(h_val, charset))
                msg.add_header(h_key, h_val)
            except Exception:
                module.warn("Skipping header '%s', unable to parse" % hdr)

    if 'X-Mailer' not in msg:
        msg.add_header('X-Mailer', 'Ansible mail module')

    addr_list = []
    for addr in [x.strip() for x in blindcopies]:
        addr_list.append(parseaddr(addr)[1])    # address only, w/o phrase

    to_list = []
    for addr in [x.strip() for x in recipients]:
        to_list.append(formataddr(parseaddr(addr)))
        addr_list.append(parseaddr(addr)[1])    # address only, w/o phrase
    msg['To'] = ", ".join(to_list)

    cc_list = []
    for addr in [x.strip() for x in copies]:
        cc_list.append(formataddr(parseaddr(addr)))
        addr_list.append(parseaddr(addr)[1])    # address only, w/o phrase
    msg['Cc'] = ", ".join(cc_list)

    part = MIMEText(body + "\n\n", _subtype=subtype, _charset=charset)
    msg.attach(part)

    # NOTE: Backware compatibility with old syntax using space as delimiter is not retained
    #       This breaks files with spaces in it :-(
    for filename in attach_files:
        try:
            part = MIMEBase('application', 'octet-stream')
            with open(filename, 'rb') as fp:
                part.set_payload(fp.read())
            encoders.encode_base64(part)
            part.add_header('Content-disposition', 'attachment', filename=os.path.basename(filename))
            msg.attach(part)
        except Exception as e:
            module.fail_json(rc=1, msg="Failed to send mail: can't attach file %s: %s" %
                             (filename, to_native(e)), exception=traceback.format_exc())

    composed = msg.as_string()

    try:
        result = smtp.sendmail(sender_addr, set(addr_list), composed)
    except Exception as e:
        module.fail_json(rc=1, msg="Failed to send mail to '%s': %s" %
                         (", ".join(set(addr_list)), to_native(e)), exception=traceback.format_exc())

    smtp.quit()

    if result:
        for key in result:
            module.warn("Failed to send mail to '%s': %s %s" % (key, result[key][0], result[key][1]))
        module.exit_json(msg='Failed to send mail to at least one recipient', result=result)

    module.exit_json(msg='Mail sent successfully', result=result)


if __name__ == '__main__':
    main()

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

import smtplib

def mail(subject='Ansible error mail', sender='root', to='root', cc=None, bcc=None, body=None):
    if not body:
        body = subject

    smtp = smtplib.SMTP('localhost')

    content = 'From: %s\n' % sender
    content += 'To: %s\n' % to
    if cc:
        content += 'Cc: %s\n' % cc
    content += 'Subject: %s\n\n' % subject
    content += body

    addresses = to.split(',')
    if cc:
        addresses += cc.split(',')
    if bcc:
        addresses += bcc.split(',')

    for address in addresses:
        smtp.sendmail(sender, address, content)

    smtp.quit()


class CallbackModule(object):

    """
    This Ansible callback plugin mails errors to interested parties.
    """

    def runner_on_failed(self, host, res, ignore_errors=False):
        if ignore_errors:
            return
        sender = 'Ansible error on %s' % host
        subject = 'Failure: %s' % res['msg'].split('\n')[0]
        mail(sender=sender, subject=subject, 
             body='''The following task failed for host %s:

%s %s

with the following error message:

%s

A complete dump of the error:

%s''' % (host, res['invocation']['module_name'], res['invocation']['module_args'], res['msg'], res)
        )

    def runner_on_error(self, host, msg):
        sender = 'Ansible: %s <root>' % host
        subject = 'Error: %s' % res['msg'].split('\n')[0]
        mail(sender=sender, subject=subject, body=msg)

    def runner_on_unreachable(self, host, res):
        sender = 'Ansible: %s <root>' % host
        subject = 'Unreachable: %s' % res.split('\n')[0]
        mail(sender=sender, subject=subject, body=res)

    def runner_on_async_failed(self, host, res, jid):
        sender = 'Ansible: %s <root>' % host
        subject = 'Async failure: %s' % res.split('\n')[0]
        mail(sender=sender, subject=subject, body=res)

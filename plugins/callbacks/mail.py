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

def mail(subject='Ansible error mail', sender='<root>', to='root', cc=None, bcc=None, body=None):
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
        sender = '"Ansible: %s" <root>' % host
        subject = 'Failed: %(module_name)s %(module_args)s' % res['invocation']
        body = 'The following task failed for host ' + host + ':\n\n%(module_name)s %(module_args)s\n\n' % res['invocation']
        if 'stdout' in res.keys() and res['stdout']:
            subject = res['stdout'].strip('\r\n').split('\n')[-1]
            body += 'with the following output in standard output:\n\n' + res['stdout'] + '\n\n'
        if 'stderr' in res.keys() and res['stderr']:
            subject = res['stderr'].strip('\r\n').split('\n')[-1]
            body += 'with the following output in standard error:\n\n' + res['stderr'] + '\n\n'
        if 'msg' in res.keys() and res['msg']:
            subject = res['msg'].strip('\r\n').split('\n')[0]
            body += 'with the following message:\n\n' + res['msg'] + '\n\n'
        body += 'A complete dump of the error:\n\n' + str(res)
        mail(sender=sender, subject=subject, body=body)
                  
    def runner_on_unreachable(self, host, res):
        sender = '"Ansible: %s" <root>' % host
        if isinstance(res, basestring):
            subject = 'Unreachable: %s' % res.strip('\r\n').split('\n')[-1]
            body = 'An error occured for host ' + host + ' with the following message:\n\n' + res
        else:
            subject = 'Unreachable: %s' % res['msg'].strip('\r\n').split('\n')[0]
            body = 'An error occured for host ' + host + ' with the following message:\n\n' + \
                   res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
        mail(sender=sender, subject=subject, body=body)

    def runner_on_async_failed(self, host, res, jid):
        sender = '"Ansible: %s" <root>' % host
        if isinstance(res, basestring):
            subject = 'Async failure: %s' % res.strip('\r\n').split('\n')[-1]
            body = 'An error occured for host ' + host + ' with the following message:\n\n' + res
        else:
            subject = 'Async failure: %s' % res['msg'].strip('\r\n').split('\n')[0]
            body = 'An error occured for host ' + host + ' with the following message:\n\n' + \
                   res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
        mail(sender=sender, subject=subject, body=body)

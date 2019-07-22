# -*- coding: utf-8 -*-
# (c) 2018 Remi Verchere <remi@verchere.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: nrdp
    type: notification
    author: "Remi VERCHERE (@rverchere)"
    short_description: post task result to a nagios server through nrdp
    description:
        - this callback send playbook result to nagios
        - nagios shall use NRDP to recive passive events
        - the passive check is sent to a dedicated host/service for ansible
    version_added: 2.8
    options:
        url:
            description: url of the nrdp server
            required: True
            env:
                - name : NRDP_URL
            ini:
                - section: callback_nrdp
                  key: url
        validate_certs:
            description: (bool) validate the SSL certificate of the nrdp server. (For HTTPS url)
            env:
                - name: NRDP_VALIDATE_CERTS
            ini:
                - section: callback_nrdp
                  key: validate_nrdp_certs
                - section: callback_nrdp
                  key: validate_certs
            default: False
            aliases: [ validate_nrdp_certs ]
        token:
            description: token to be allowed to push nrdp events
            required: True
            env:
                - name: NRDP_TOKEN
            ini:
                - section: callback_nrdp
                  key: token
        hostname:
            description: hostname where the passive check is linked to
            required: True
            env:
                - name : NRDP_HOSTNAME
            ini:
                - section: callback_nrdp
                  key: hostname
        servicename:
            description: service where the passive check is linked to
            required: True
            env:
                - name : NRDP_SERVICENAME
            ini:
                - section: callback_nrdp
                  key: servicename
'''

import os
import json

from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    '''
    send ansible-playbook to Nagios server using nrdp protocol
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'nrdp'
    CALLBACK_NEEDS_WHITELIST = True

    # Nagios states
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    def __init__(self):
        super(CallbackModule, self).__init__()

        self.printed_playbook = False
        self.playbook_name = None
        self.play = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.url = self.get_option('url')
        if not self.url.endswith('/'):
            self.url += '/'
        self.token = self.get_option('token')
        self.hostname = self.get_option('hostname')
        self.servicename = self.get_option('servicename')
        self.validate_nrdp_certs = self.get_option('validate_certs')

        if (self.url or self.token or self.hostname or
                self.servicename) is None:
            self._display.warning("NRDP callback wants the NRDP_URL,"
                                  " NRDP_TOKEN, NRDP_HOSTNAME,"
                                  " NRDP_SERVICENAME"
                                  " environment variables'."
                                  " The NRDP callback plugin is disabled.")
            self.disabled = True

    def _send_nrdp(self, state, msg):
        '''
        nrpd service check send XMLDATA like this:
        <?xml version='1.0'?>
            <checkresults>
                <checkresult type='service'>
                    <hostname>somehost</hostname>
                    <servicename>someservice</servicename>
                    <state>1</state>
                    <output>WARNING: Danger Will Robinson!|perfdata</output>
                </checkresult>
            </checkresults>
        '''
        xmldata = "<?xml version='1.0'?>\n"
        xmldata += "<checkresults>\n"
        xmldata += "<checkresult type='service'>\n"
        xmldata += "<hostname>%s</hostname>\n" % self.hostname
        xmldata += "<servicename>%s</servicename>\n" % self.servicename
        xmldata += "<state>%d</state>\n" % state
        xmldata += "<output>%s</output>\n" % msg
        xmldata += "</checkresult>\n"
        xmldata += "</checkresults>\n"

        body = {
            'cmd': 'submitcheck',
            'token': self.token,
            'XMLDATA': bytes(xmldata)
        }

        try:
            response = open_url(self.url,
                                data=urlencode(body),
                                method='POST',
                                validate_certs=self.validate_nrdp_certs)
            return response.read()
        except Exception as ex:
            self._display.warning("NRDP callback cannot send result {0}".format(ex))

    def v2_playbook_on_play_start(self, play):
        '''
        Display Playbook and play start messages
        '''
        self.play = play

    def v2_playbook_on_stats(self, stats):
        '''
        Display info about playbook statistics
        '''
        name = self.play
        gstats = ""
        hosts = sorted(stats.processed.keys())
        critical = warning = 0
        for host in hosts:
            stat = stats.summarize(host)
            gstats += "'%s_ok'=%d '%s_changed'=%d \
                       '%s_unreachable'=%d '%s_failed'=%d " % \
                (host, stat['ok'], host, stat['changed'],
                 host, stat['unreachable'], host, stat['failures'])
            # Critical when failed tasks or unreachable host
            critical += stat['failures']
            critical += stat['unreachable']
            # Warning when changed tasks
            warning += stat['changed']

        msg = "%s | %s" % (name, gstats)
        if critical:
            # Send Critical
            self._send_nrdp(self.CRITICAL, msg)
        elif warning:
            # Send Warning
            self._send_nrdp(self.WARNING, msg)
        else:
            # Send OK
            self._send_nrdp(self.OK, msg)

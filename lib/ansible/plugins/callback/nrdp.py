# -*- coding: utf-8 -*-

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
    version_added: 2.5
    requirements:
        - requests
    options:
        url:
            description: url of the nrdp server
            required: True
            env:
                - name : NRDP_URL
        token:
            description: token to be allowed to push nrdp events
            required: True
            env:
                - name: NRDP_TOKEN
        hostname:
            description: hostname where the passive check is linked to
            required: True
            env:
                - name : NRDP_ANSIBLE_HOSTNAME
        servicename:
            description: service where the passive check is linked to
            required: True
            env:
                - name : NRDP_ANSIBLE_SERVICENAME
'''

import os

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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

        if not HAS_REQUESTS:
            self._display.warning(
                "The required python requests library is not installed."
                " The NRDP callback plugin is disabled.")
            self.disabled = True

        self.url = os.getenv("NRDP_URL")
        if not self.url.endswith('/'):
            self.url += '/'
        self.token = os.getenv("NRDP_TOKEN")
        self.hostname = os.getenv("NRDP_ANSIBLE_HOSTNAME")
        self.servicename = os.getenv("NRDP_ANSIBLE_SERVICENAME")

        if (self.url or self.token or self.hostname or
                self.servicename) is None:
            self._display.warning("NRDP callback wants the NRDP_URL,"
                " NRDP_TOKEN, NRDP_ANSIBLE_HOSTNAME, NRDP_ANSIBLE_SERVICENAME"
                " environment variables'."
                " The NRDP callback plugin is disabled.")
            self.disabled = True

        self.play = None

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

        try:
            # disable urllib3 and ssl warnings
            if hasattr(requests.packages.urllib3, 'disable_warnings'):
                requests.packages.urllib3.disable_warnings()
            response = requests.post(
                self.url,
                data={
                    'cmd': 'submitcheck',
                    'token': self.token,
                    'XMLDATA': bytes(xmldata)
                },
                verify=False,
                stream=False
            )
            if not response.ok:
                self._display.warning("NRDP callback cannot send result.")
        except:
            self._display.warning("NRDP callback cannot send result.")

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

        msg = "%s|%s" % (name, gstats)
        if critical:
            # Send Critical
            self._send_nrdp(self.CRITICAL, msg)
        elif warning:
            # Send Warning
            self._send_nrdp(self.WARNING, msg)
        else:
            # Send OK
            self._send_nrdp(self.OK, msg)

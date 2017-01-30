# Ansible CallBack module for Jabber (XMPP)
# Copyright (C) 2016 maxn nikolaev.makc@gmail.com
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

HAS_XMPP = True
try:
    import xmpp
except ImportError:
    HAS_XMPP = False

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'jabber'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        if not HAS_XMPP:
            self._display.warning("The required python xmpp library (xmpppy) is not installed."
                " pip install git+https://github.com/ArchipelProject/xmpppy")
            self.disabled = True

        self.serv = os.getenv('JABBER_SERV')
        self.j_user = os.getenv('JABBER_USER')
        self.j_pass = os.getenv('JABBER_PASS')
        self.j_to = os.getenv('JABBER_TO')

        if (self.j_user or self.j_pass or self.serv ) is None:
            self.disabled = True
            self._display.warning ('Jabber CallBack want JABBER_USER and JABBER_PASS env variables')

    def send_msg(self, msg):
        """Send message"""
        jid = xmpp.JID(self.j_user)
        client = xmpp.Client(self.serv,debug=[])
        client.connect(server=(self.serv,5222))
        client.auth(jid.getNode(), self.j_pass, resource=jid.getResource())
        message = xmpp.Message(self.j_to, msg)
        message.setAttr('type', 'chat')
        client.send(message)
        client.disconnect()

    def v2_runner_on_ok(self, result):
        self._clean_results(result._result, result._task.action)
        self.debug = self._dump_results(result._result)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task

    def v2_playbook_on_play_start(self, play):
        """Display Playbook and play start messages"""
        self.play = play
        name = play.name
        self.send_msg("Ansible starting play: %s" % (name))

    def playbook_on_stats(self, stats):
        name = self.play
        hosts = sorted(stats.processed.keys())
        failures = False
        unreachable = False
        for h in hosts:
            s = stats.summarize(h)
            if s['failures'] > 0:
                failures = True
            if s['unreachable'] > 0:
                unreachable = True

        if failures or unreachable:
            out = self.debug
            self.send_msg("%s: Failures detected \n%s \nHost: %s\n Failed at:\n%s" % (name, self.task, h, out))
        else:
            out = self.debug
            self.send_msg("Great! \n Playbook %s completed:\n%s \n Last task debug:\n %s" % (name,s, out))


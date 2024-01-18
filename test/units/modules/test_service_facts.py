# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import unittest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible.modules.service_facts import AIXScanService


# AIX # lssrc -a
LSSRC_OUTPUT = """
Subsystem         Group            PID          Status
 sendmail         mail             5243302      active
 syslogd          ras              5636528      active
 portmap          portmap          5177768      active
 snmpd            tcpip            5308844      active
 hostmibd         tcpip            5374380      active
 snmpmibd         tcpip            5439918      active
 aixmibd          tcpip            5505456      active
 nimsh            nimclient        5571004      active
 aso                               6029758      active
 biod             nfs              6357464      active
 nfsd             nfs              5701906      active
 rpc.mountd       nfs              6488534      active
 rpc.statd        nfs              7209216      active
 rpc.lockd        nfs              7274988      active
 qdaemon          spooler          6816222      active
 writesrv         spooler          6685150      active
 clcomd           caa              7471600      active
 sshd             ssh              7602674      active
 pfcdaemon                         7012860      active
 ctrmc            rsct             6947312      active
 IBM.HostRM       rsct_rm          14418376     active
 IBM.ConfigRM     rsct_rm          6160674      active
 IBM.DRM          rsct_rm          14680550     active
 IBM.MgmtDomainRM rsct_rm          14090676     active
 IBM.ServiceRM    rsct_rm          13828542     active
 cthats           cthats           13959668     active
 cthags           cthags           14025054     active
 IBM.StorageRM    rsct_rm          12255706     active
 inetd            tcpip            12517828     active
 lpd              spooler                       inoperative
 keyserv          keyserv                       inoperative
 ypbind           yp                            inoperative
 gsclvmd                                        inoperative
 cdromd                                         inoperative
 ndpd-host        tcpip                         inoperative
 ndpd-router      tcpip                         inoperative
 netcd            netcd                         inoperative
 tftpd            tcpip                         inoperative
 routed           tcpip                         inoperative
 mrouted          tcpip                         inoperative
 rsvpd            qos                           inoperative
 policyd          qos                           inoperative
 timed            tcpip                         inoperative
 iptrace          tcpip                         inoperative
 dpid2            tcpip                         inoperative
 rwhod            tcpip                         inoperative
 pxed             tcpip                         inoperative
 binld            tcpip                         inoperative
 xntpd            tcpip                         inoperative
 gated            tcpip                         inoperative
 dhcpcd           tcpip                         inoperative
 dhcpcd6          tcpip                         inoperative
 dhcpsd           tcpip                         inoperative
 dhcpsdv6         tcpip                         inoperative
 dhcprd           tcpip                         inoperative
 dfpd             tcpip                         inoperative
 named            tcpip                         inoperative
 automountd       autofs                        inoperative
 nfsrgyd          nfs                           inoperative
 gssd             nfs                           inoperative
 cpsd             ike                           inoperative
 tmd              ike                           inoperative
 isakmpd                                        inoperative
 ikev2d                                         inoperative
 iked             ike                           inoperative
 clconfd          caa                           inoperative
 ksys_vmmon                                     inoperative
 nimhttp                                        inoperative
 IBM.SRVPROXY     ibmsrv                        inoperative
 ctcas            rsct                          inoperative
 IBM.ERRM         rsct_rm                       inoperative
 IBM.AuditRM      rsct_rm                       inoperative
 isnstgtd         isnstgtd                      inoperative
 IBM.LPRM         rsct_rm                       inoperative
 cthagsglsm       cthags                        inoperative
"""


class TestAIXScanService(unittest.TestCase):

    def setUp(self):
        self.mock1 = patch.object(basic.AnsibleModule, 'get_bin_path', return_value='/usr/sbin/lssrc')
        self.mock1.start()
        self.addCleanup(self.mock1.stop)
        self.mock2 = patch.object(basic.AnsibleModule, 'run_command', return_value=(0, LSSRC_OUTPUT, ''))
        self.mock2.start()
        self.addCleanup(self.mock2.stop)
        self.mock3 = patch('platform.system', return_value='AIX')
        self.mock3.start()
        self.addCleanup(self.mock3.stop)

    def test_gather_services(self):
        svcmod = AIXScanService(basic.AnsibleModule)
        result = svcmod.gather_services()

        self.assertIsInstance(result, dict)

        self.assertIn('IBM.HostRM', result)
        self.assertEqual(result['IBM.HostRM'], {
            'name': 'IBM.HostRM',
            'source': 'src',
            'state': 'running',
        })
        self.assertIn('IBM.AuditRM', result)
        self.assertEqual(result['IBM.AuditRM'], {
            'name': 'IBM.AuditRM',
            'source': 'src',
            'state': 'stopped',
        })

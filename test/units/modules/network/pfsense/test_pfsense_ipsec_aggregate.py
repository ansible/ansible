# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from units.modules.utils import set_module_args
from ansible.modules.network.pfsense import pfsense_ipsec_aggregate

from .pfsense_module import TestPFSenseModule


class TestPFSenseIpsecAggregateModule(TestPFSenseModule):

    module = pfsense_ipsec_aggregate

    def __init__(self, *args, **kwargs):
        super(TestPFSenseIpsecAggregateModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_ipsec_aggregate_config.xml'

    def assert_find_ipsec(self, ipsec):
        """ test if an ipsec tunnel exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('ipsec')
        if parent_tag is None:
            self.fail('Unable to find tag ipsec')

        found = False
        for ipsec_elt in parent_tag:
            if ipsec_elt.tag != 'phase1':
                continue

            if ipsec_elt.find('descr').text == ipsec:
                found = True
                break

        if not found:
            self.fail('Ipsec tunnel not found: ' + ipsec)

    def assert_not_find_ipsec(self, ipsec):
        """ test if an ipsec tunnel does not exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('ipsec')
        if parent_tag is None:
            self.fail('Unable to find tag ipsec')

        found = False
        for ipsec_elt in parent_tag:
            if ipsec_elt.tag != 'phase1':
                continue

            if ipsec_elt.find('descr').text == ipsec:
                found = True
                break

        if found:
            self.fail('Ipsec tunnel found: ' + ipsec)

    ############
    # as we rely on sub modules for modifying the xml
    # we dont perform checks on the xml modifications
    # we just test the output
    def test_ipsec_aggregate_ipsecs(self):
        """ test creation of a some tunnels """
        args = dict(
            purge_ipsecs=False,
            aggregated_ipsecs=[
                dict(descr='t1', interface='wan', remote_gateway='1.3.3.1', iketype='ikev2', authentication_method='pre_shared_key', preshared_key='azerty123'),
                dict(descr='t2', interface='wan', remote_gateway='1.3.3.2', iketype='ikev2', authentication_method='pre_shared_key', preshared_key='qwerty123'),
                dict(descr='test_tunnel2', state='absent'),
                dict(
                    descr='test_tunnel', interface='lan_100', remote_gateway='1.2.4.8', iketype='ikev2',
                    authentication_method='pre_shared_key', preshared_key='0123456789'
                ),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_ipsecs = []
        result_ipsecs.append(
            "create ipsec 't1', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.3.3.1', authentication_method='pre_shared_key', "
            "preshared_key='azerty123', myid_type='myaddress', peerid_type='peeraddress', lifetime='28800', disable_rekey=False, margintime='', "
            "mobike='off', responderonly=False, nat_traversal='on', enable_dpd=True, dpd_delay='10', dpd_maxfail='5'"
        )
        result_ipsecs.append(
            "create ipsec 't2', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.3.3.2', authentication_method='pre_shared_key', "
            "preshared_key='qwerty123', myid_type='myaddress', peerid_type='peeraddress', lifetime='28800', disable_rekey=False, margintime='', "
            "mobike='off', responderonly=False, nat_traversal='on', enable_dpd=True, dpd_delay='10', dpd_maxfail='5'"
        )
        result_ipsecs.append("delete ipsec 'test_tunnel2'")
        result_ipsecs.append("update ipsec 'test_tunnel' set preshared_key='0123456789'")

        self.assertEqual(result['result_ipsecs'], result_ipsecs)
        self.assert_find_ipsec('t1')
        self.assert_find_ipsec('t2')
        self.assert_not_find_ipsec('test_tunnel2')
        self.assert_find_ipsec('test_tunnel')

    def test_ipsec_aggregate_ipsecs_purge(self):
        """ test creation of a some tunnels with purge """
        args = dict(
            purge_ipsecs=True,
            aggregated_ipsecs=[
                dict(descr='t1', interface='wan', remote_gateway='1.3.3.1', iketype='ikev2', authentication_method='pre_shared_key', preshared_key='azerty123'),
                dict(descr='t2', interface='wan', remote_gateway='1.3.3.2', iketype='ikev2', authentication_method='pre_shared_key', preshared_key='qwerty123'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_ipsecs = []
        result_ipsecs.append(
            "create ipsec 't1', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.3.3.1', authentication_method='pre_shared_key', "
            "preshared_key='azerty123', myid_type='myaddress', peerid_type='peeraddress', lifetime='28800', disable_rekey=False, margintime='', "
            "mobike='off', responderonly=False, nat_traversal='on', enable_dpd=True, dpd_delay='10', dpd_maxfail='5'"
        )
        result_ipsecs.append(
            "create ipsec 't2', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.3.3.2', authentication_method='pre_shared_key', "
            "preshared_key='qwerty123', myid_type='myaddress', peerid_type='peeraddress', lifetime='28800', disable_rekey=False, margintime='', "
            "mobike='off', responderonly=False, nat_traversal='on', enable_dpd=True, dpd_delay='10', dpd_maxfail='5'"
        )
        result_ipsecs.append("delete ipsec 'test_tunnel'")
        result_ipsecs.append("delete ipsec 'test_tunnel2'")

        self.assertEqual(result['result_ipsecs'], result_ipsecs)
        self.assert_find_ipsec('t1')
        self.assert_find_ipsec('t2')
        self.assert_not_find_ipsec('test_tunnel')
        self.assert_not_find_ipsec('test_tunnel2')

    def test_ipsec_aggregate_proposals(self):
        """ test creation of a some proposals """
        args = dict(
            purge_ipsec_proposals=False,
            aggregated_ipsec_proposals=[
                dict(descr='test_tunnel', encryption='aes', key_length=128, hash='md5', dhgroup=14),
                dict(descr='test_tunnel2', encryption='cast128', hash='sha512', dhgroup=14),
                dict(descr='test_tunnel', encryption='aes', key_length=128, hash='sha256', dhgroup=14, state='absent'),
                dict(descr='test_tunnel2', encryption='blowfish', key_length=256, hash='aesxcbc', dhgroup=14, state='absent'),
            ]
        )
        set_module_args(args)
        self.execute_module(changed=True)
        result = self.execute_module(changed=True)
        result_ipsec_proposals = []
        result_ipsec_proposals.append("create ipsec_proposal 'test_tunnel', encryption='aes', key_length=128, hash='md5', dhgroup='14'")
        result_ipsec_proposals.append("create ipsec_proposal 'test_tunnel2', encryption='cast128', hash='sha512', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel', encryption='aes', key_length=128, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel2', encryption='blowfish', key_length=256, hash='aesxcbc', dhgroup='14'")

        self.assertEqual(result['result_ipsec_proposals'], result_ipsec_proposals)

    def test_ipsec_aggregate_proposals_purge(self):
        """ test creation of a some proposals with purge """
        args = dict(
            purge_ipsec_proposals=True,
            aggregated_ipsec_proposals=[
                dict(descr='test_tunnel', encryption='aes', key_length=128, hash='md5', dhgroup=14),
                dict(descr='test_tunnel2', encryption='cast128', hash='sha512', dhgroup=14),
            ]
        )
        set_module_args(args)
        self.execute_module(changed=True)
        result = self.execute_module(changed=True)
        result_ipsec_proposals = []
        result_ipsec_proposals.append("create ipsec_proposal 'test_tunnel', encryption='aes', key_length=128, hash='md5', dhgroup='14'")
        result_ipsec_proposals.append("create ipsec_proposal 'test_tunnel2', encryption='cast128', hash='sha512', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel', encryption='aes', key_length=128, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel', encryption='aes', key_length=256, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel', encryption='blowfish', key_length=256, hash='aesxcbc', dhgroup='14'")

        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel2', encryption='aes', key_length=128, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel2', encryption='aes', key_length=256, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel2', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'")
        result_ipsec_proposals.append("delete ipsec_proposal 'test_tunnel2', encryption='blowfish', key_length=256, hash='aesxcbc', dhgroup='14'")

        self.assertEqual(result['result_ipsec_proposals'], result_ipsec_proposals)

    def test_ipsec_aggregate_p2s(self):
        """ test creation of a some p2s """
        args = dict(
            purge_ipsec_p2s=False,
            aggregated_ipsec_p2s=[
                dict(descr='p2_1', p1_descr='test_tunnel', mode='tunnel', local='1.2.3.4/24', remote='10.20.30.40/24', aes=True, aes_len='auto', sha256=True),
                dict(descr='p2_2', p1_descr='test_tunnel', mode='tunnel', local='1.2.3.4/24', remote='10.20.30.50/24', aes=True, aes_len='auto', sha256=True),
                dict(
                    descr='one_p2', p1_descr='test_tunnel', mode='tunnel', local='lan', remote='10.20.30.60/24',
                    aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True'
                ),
                dict(descr='another_p2', p1_descr='test_tunnel', state='absent')
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_ipsec_p2s = []
        result_ipsec_p2s.append(
            "create ipsec_p2 'p2_1' on 'test_tunnel', disabled=False, mode='tunnel', local='1.2.3.4/24', remote='10.20.30.40/24', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        result_ipsec_p2s.append(
            "create ipsec_p2 'p2_2' on 'test_tunnel', disabled=False, mode='tunnel', local='1.2.3.4/24', remote='10.20.30.50/24', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        result_ipsec_p2s.append("update ipsec_p2 'one_p2' on 'test_tunnel' set remote='10.20.30.60/24'")
        result_ipsec_p2s.append("delete ipsec_p2 'another_p2' on 'test_tunnel'")

        self.assertEqual(result['result_ipsec_p2s'], result_ipsec_p2s)

    def test_ipsec_aggregate_p2s_purge(self):
        """ test creation of a some p2s with purge """
        args = dict(
            purge_ipsec_p2s=True,
            aggregated_ipsec_p2s=[
                dict(descr='p2_1', p1_descr='test_tunnel', mode='tunnel', local='1.2.3.4/24', remote='10.20.30.40/24', aes=True, aes_len='auto', sha256=True),
                dict(descr='p2_2', p1_descr='test_tunnel', mode='tunnel', local='1.2.3.4/24', remote='10.20.30.50/24', aes=True, aes_len='auto', sha256=True),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_ipsec_p2s = []
        result_ipsec_p2s.append(
            "create ipsec_p2 'p2_1' on 'test_tunnel', disabled=False, mode='tunnel', local='1.2.3.4/24', remote='10.20.30.40/24', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        result_ipsec_p2s.append(
            "create ipsec_p2 'p2_2' on 'test_tunnel', disabled=False, mode='tunnel', local='1.2.3.4/24', remote='10.20.30.50/24', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        result_ipsec_p2s.append("delete ipsec_p2 'one_p2' on 'test_tunnel'")
        result_ipsec_p2s.append("delete ipsec_p2 'another_p2' on 'test_tunnel'")
        result_ipsec_p2s.append("delete ipsec_p2 'third_p2' on 'test_tunnel'")
        result_ipsec_p2s.append("delete ipsec_p2 'nat_p2' on 'test_tunnel'")

        self.assertEqual(result['result_ipsec_p2s'], result_ipsec_p2s)

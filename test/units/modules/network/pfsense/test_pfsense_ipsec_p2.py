# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_ipsec_p2
from .pfsense_module import TestPFSenseModule


class TestPFSenseIpsecP2Module(TestPFSenseModule):

    module = pfsense_ipsec_p2

    def __init__(self, *args, **kwargs):
        super(TestPFSenseIpsecP2Module, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_ipsec_p2_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'p1_descr', 'disabled', 'mode', 'local', 'nat', 'remote', 'apply', 'protocol', 'pfsgroup', 'lifetime', 'pinghost']
        fields += ['aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', 'des', 'cast128']
        fields += ['aes_len', 'aes128gcm_len', 'aes192gcm_len', 'aes256gcm_len', 'blowfish_len']
        fields += ['md5', 'sha1', 'sha256', 'sha384', 'sha512', 'aesxcbc']
        return fields

    ##############
    # tests utils
    #
    def get_phase1_elt(self, descr, absent=False):
        """ get phase1 """
        elt_filter = {}
        elt_filter['descr'] = descr
        return self.assert_has_xml_tag('ipsec', elt_filter, absent=absent)

    def get_target_elt(self, phase2, absent=False):
        """ get the generated phase2 xml definition """
        phase1_elt = self.get_phase1_elt(phase2['p1_descr'])

        elt_filter = {}
        elt_filter['descr'] = phase2['descr']
        elt_filter['ikeid'] = phase1_elt.find('ikeid').text
        return self.assert_has_xml_tag('ipsec', elt_filter, absent=absent)

    @staticmethod
    def get_enc_elt(phase2_elt, enc_name):
        """ get encryption """
        for elt in phase2_elt:
            if elt.tag != 'encryption-algorithm-option':
                continue
            if elt.find('name').text == enc_name:
                return elt
        return None

    def check_enc(self, phase2, phase2_elt, enc_name, param_name):
        """ check encryption """
        enc_elt = self.get_enc_elt(phase2_elt, enc_name)
        if phase2.get(param_name):
            if enc_elt is None:
                self.fail('Encryption named {0} not found'.format(enc_name))
            if phase2.get(param_name + '_len') is not None:
                keylen_elt = enc_elt.find('keylen')
                if keylen_elt is None:
                    self.fail('Key length not found for encryption named {0}'.format(enc_name))
                self.assertEqual(keylen_elt.text, phase2[param_name + '_len'])
        else:
            if enc_elt is not None:
                self.fail('Encryption named {0} found'.format(enc_name))

    @staticmethod
    def get_hash_elt(phase2_elt, hash_name):
        """ get hash """
        for elt in phase2_elt:
            if elt.tag != 'hash-algorithm-option':
                continue
            if elt.text == hash_name:
                return elt
        return None

    def check_hash(self, phase2, phase2_elt, hash_name, param_name):
        """ check hash """
        hash_elt = self.get_hash_elt(phase2_elt, hash_name)
        if phase2.get(param_name):
            if hash_elt is None:
                self.fail('Hash algorithm named {0} not found'.format(hash_name))
        else:
            if hash_elt is not None:
                self.fail('Hash algorithm named {0} found'.format(hash_name))

    def param_to_address(self, address):
        """ hardcoded addresses """
        ret = dict()
        if address in ['1.2.3.1', '1.2.3.2']:
            ret['type'] = 'address'
            ret['address'] = address
            ret['type'] = 'address'
            ret['address'] = address
        elif address == '1.2.3.4/24':
            ret['type'] = 'network'
            ret['address'] = '1.2.3.4'
            ret['netbits'] = '24'
        elif address == '10.20.30.40/24':
            ret['type'] = 'network'
            ret['address'] = '10.20.30.40'
            ret['netbits'] = '24'
        elif address == '10.20.30.50/24':
            ret['type'] = 'network'
            ret['address'] = '10.20.30.50'
            ret['netbits'] = '24'
        elif address in ['lan_100', 'lan']:
            ret['type'] = self.unalias_interface(address)
        else:
            self.fail('Please add address {0} to param_to_address'.format(address))
        return ret

    def check_address(self, phase2, phase2_elt, elt_name, param_name):
        """ check address """
        if phase2.get(param_name) is None:
            if phase2_elt.find(elt_name) is not None:
                self.fail('Address type {0} found'.format(elt_name))
        else:
            addr_elt = phase2_elt.find(elt_name)
            if addr_elt is None:
                self.fail('Address type {0} not found'.format(elt_name))

            address = self.param_to_address(phase2[param_name])
            for param in address.keys():
                elt = addr_elt.find(param)
                if elt is None:
                    self.fail('Address param {0} not found'.format(param))
                self.assertEqual(elt.text, address[param])

            params = address.keys()
            for elt in addr_elt:
                if elt.tag not in params:
                    self.fail('Address param{0} found'.format(elt.tag))

    def check_target_elt(self, phase2, phase2_elt):
        """ test the xml definition of phase2 elt """
        # bools
        if phase2.get('disabled'):
            self.assert_xml_elt_is_none_or_empty(phase2_elt, 'disabled')
        else:
            self.assert_not_find_xml_elt(phase2_elt, 'disabled')

        self.assert_xml_elt_equal(phase2_elt, 'mode', phase2['mode'])
        if phase2.get('procotol') is not None:
            self.assert_xml_elt_equal(phase2_elt, 'protocol', phase2['protocol'])
        else:
            self.assert_xml_elt_equal(phase2_elt, 'protocol', 'esp')
        if phase2.get('pfsgroup') is not None:
            self.assert_xml_elt_equal(phase2_elt, 'pfsgroup', phase2['pfsgroup'])
        else:
            self.assert_xml_elt_equal(phase2_elt, 'pfsgroup', '14')

        if phase2.get('lifetime') is not None:
            if phase2['lifetime'] == 0:
                self.assert_xml_elt_is_none_or_empty(phase2_elt, 'lifetime')
            else:
                self.assert_xml_elt_equal(phase2_elt, 'lifetime', str(phase2['lifetime']))
        else:
            self.assert_xml_elt_equal(phase2_elt, 'lifetime', '3600')

        if phase2.get('pinghost') is not None:
            self.assert_xml_elt_equal(phase2_elt, 'pinghost', str(phase2['pinghost']))
        else:
            self.assert_xml_elt_is_none_or_empty(phase2_elt, 'pinghost')

        # encryptions
        self.check_enc(phase2, phase2_elt, 'aes', 'aes')
        self.check_enc(phase2, phase2_elt, 'aes128gcm', 'aes128gcm')
        self.check_enc(phase2, phase2_elt, 'aes192gcm', 'aes192gcm')
        self.check_enc(phase2, phase2_elt, 'aes256gcm', 'aes256gcm')
        self.check_enc(phase2, phase2_elt, 'blowfish', 'blowfish')
        self.check_enc(phase2, phase2_elt, '3des', 'des')
        self.check_enc(phase2, phase2_elt, 'cast128', 'cast128')

        # hashes
        self.check_hash(phase2, phase2_elt, 'hmac_md5', 'md5')
        self.check_hash(phase2, phase2_elt, 'hmac_sha1', 'sha1')
        self.check_hash(phase2, phase2_elt, 'hmac_sha256', 'sha256')
        self.check_hash(phase2, phase2_elt, 'hmac_sha384', 'sha384')
        self.check_hash(phase2, phase2_elt, 'hmac_sha512', 'sha512')
        self.check_hash(phase2, phase2_elt, 'aesxcbc', 'aesxcbc')

        self.check_address(phase2, phase2_elt, 'localid', 'local')
        self.check_address(phase2, phase2_elt, 'remoteid', 'remote')
        self.check_address(phase2, phase2_elt, 'natlocalid', 'nat')

    ##############
    # tests
    #
    def test_phase2_create_vti(self):
        """ test creation of a new phase2 in vti mode """
        phase2 = dict(p1_descr='test_tunnel', descr='test_p2', mode='vti', local='1.2.3.1', remote='1.2.3.2', aes='True', aes_len='auto', sha256='True')
        command = (
            "create ipsec_p2 'test_p2' on 'test_tunnel', disabled=False, mode='vti', local='1.2.3.1', remote='1.2.3.2', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        self.do_module_test(phase2, command=command)

    def test_phase2_create_tunnel(self):
        """ test creation of a new phase2 in tunnel mode """
        phase2 = dict(p1_descr='test_tunnel', descr='test_p2', mode='tunnel', local='lan_100', remote='1.2.3.4/24', aes='True', aes_len='auto', sha256='True')
        command = (
            "create ipsec_p2 'test_p2' on 'test_tunnel', disabled=False, mode='tunnel', local='lan_100', remote='1.2.3.4/24', "
            "aes=True, aes_len='auto', sha256=True, pfsgroup='14', lifetime=3600"
        )
        self.do_module_test(phase2, command=command)

    def test_phase2_delete(self):
        """ test deletion of a phase2 """
        phase2 = dict(p1_descr='test_tunnel', descr='one_p2', state='absent')
        command = "delete ipsec_p2 'one_p2' on 'test_tunnel'"
        self.do_module_test(phase2, delete=True, command=command)

    def test_phase2_update_noop(self):
        """ test not updating a phase2 """
        phase2 = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        self.do_module_test(phase2, changed=False)

    def test_phase2_update_aes_len(self):
        """ test update aes """
        phase2 = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='10.20.30.40/24',
            aes='True', aes_len='auto', aes128gcm=True, aes128gcm_len='128', sha256='True')
        command = "update ipsec_p2 'one_p2' on 'test_tunnel' set aes_len='auto'"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_disable_aes(self):
        """ test removing aes """
        phase2 = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='10.20.30.40/24',
            aes128gcm=True, aes128gcm_len='128', sha256='True')
        command = "update ipsec_p2 'one_p2' on 'test_tunnel' set aes=False, aes_len=none"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_set_3des(self):
        """ test enabling 3des """
        phase2 = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', des=True, sha256='True')
        command = "update ipsec_p2 'one_p2' on 'test_tunnel' set des=True"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_remove_3des(self):
        """ test disabling 3des """
        phase2 = dict(
            p1_descr='test_tunnel', descr='another_p2', mode='tunnel', local='lan', remote='10.20.30.50/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', des=False, sha256='True')
        command = "update ipsec_p2 'another_p2' on 'test_tunnel' set des=False"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_remove_sha256(self):
        """ test disabling sha256 """
        phase2 = dict(
            p1_descr='test_tunnel', descr='another_p2', mode='tunnel', local='lan', remote='10.20.30.50/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', des=True, sha512='True')
        command = "update ipsec_p2 'another_p2' on 'test_tunnel' set sha256=False, sha512=True"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_change_address(self):
        """ test changing address """
        phase2 = dict(
            p1_descr='test_tunnel', descr='third_p2', mode='tunnel', local='lan_100', remote='10.20.30.50/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', des=True, sha256='True')
        command = "update ipsec_p2 'third_p2' on 'test_tunnel' set local='lan_100'"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_set_nat(self):
        """ test setting nat """
        phase2 = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='10.20.30.40/24', nat='1.2.3.4/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        command = "update ipsec_p2 'one_p2' on 'test_tunnel' set nat='1.2.3.4/24'"
        self.do_module_test(phase2, command=command)

    def test_phase2_update_remove_nat(self):
        """ test removing nat """
        phase2 = dict(
            p1_descr='test_tunnel', descr='nat_p2', mode='tunnel', local='lan', remote='1.2.3.4/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        command = "update ipsec_p2 'nat_p2' on 'test_tunnel' set nat=none"
        self.do_module_test(phase2, command=command)

    def test_phase2_inexistent_tunnel(self):
        """ test error with inexistent tunnel """
        ipsec = dict(
            p1_descr='inexistent_tunnel', descr='nat_p2', mode='tunnel', local='lan', remote='1.2.3.4/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'No ipsec tunnel named inexistent_tunnel'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_no_encryption(self):
        """ test error with no encryption """
        ipsec = dict(
            p1_descr='test_tunnel', descr='nat_p2', mode='tunnel', local='lan', remote='1.2.3.4/24', sha256='True')
        msg = 'At least one encryption algorithm must be selected.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_no_hash(self):
        """ test error with no hash """
        ipsec = dict(
            p1_descr='test_tunnel', descr='nat_p2', mode='tunnel', local='lan', remote='1.2.3.4/24', cast128='True')
        msg = 'At least one hashing algorithm needs to be selected.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_vti_lan(self):
        """ test error on vti address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='nat_p2', mode='vti', local='lan', remote='1.2.3.4', cast128='True', sha256='True')
        msg = 'VTI requires a valid local network or IP address for its endpoint address.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_vti_lan2(self):
        """ test error on vti address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='nat_p2', mode='vti', local='1.2.3.4', remote='lan', cast128='True', sha256='True')
        msg = 'VTI requires a valid remote IP address for its endpoint address.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel6_remote(self):
        """ test error on tunnel6 address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel6', local='lan', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv6 address or network must be specified in remote with tunnel6.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel6_remote2(self):
        """ test error on tunnel6 address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel6', local='lan', remote='1.2.3.4',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv6 address or network must be specified in remote with tunnel6.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel6_local(self):
        """ test error on tunnel6 address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel6', local='1.2.3.4/24', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv6 address or network must be specified in local with tunnel6.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel_remote(self):
        """ test error on tunnel address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='fd69:81a5:a5:7396:0:0:0:0',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv4 address or network must be specified in remote with tunnel.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel_remote2(self):
        """ test error on tunnel address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='lan', remote='fd69:81a5:a5:7396:0:0:0:0/64',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv4 address or network must be specified in remote with tunnel.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_tunnel_local(self):
        """ test error on tunnel address """
        ipsec = dict(
            p1_descr='test_tunnel', descr='one_p2', mode='tunnel', local='fd69:81a5:a5:7396:0:0:0:0', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'A valid IPv4 address or network must be specified in local with tunnel.'
        self.do_module_test(ipsec, msg=msg, failed=True)

    def test_phase2_duplicate(self):
        """ test error duplicate local/remote definition """
        phase2 = dict(
            p1_descr='test_tunnel', descr='duplicate_p2', mode='tunnel', local='lan', remote='10.20.30.40/24',
            aes='True', aes_len='128', aes128gcm=True, aes128gcm_len='128', sha256='True')
        msg = 'Phase2 with this Local/Remote networks combination is already defined for this Phase1.'
        self.do_module_test(phase2, msg=msg, failed=True)

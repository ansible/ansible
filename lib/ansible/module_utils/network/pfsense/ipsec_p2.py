# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase
from copy import deepcopy

IPSEC_P2_ARGUMENT_SPEC = dict(
    apply=dict(default=True, type='bool'),
    state=dict(default='present', choices=['present', 'absent']),
    descr=dict(required=True, type='str'),
    p1_descr=dict(required=True, type='str'),

    disabled=dict(default=False, type='bool'),
    mode=dict(choices=['tunnel', 'tunnel6', 'transport', 'vti'], type='str'),
    protocol=dict(default='esp', choices=['esp', 'ah'], type='str'),

    # addresses
    local=dict(required=False, type='str'),
    nat=dict(required=False, type='str'),
    remote=dict(required=False, type='str'),

    # encryptions
    aes=dict(required=False, type='bool'),
    aes128gcm=dict(required=False, type='bool'),
    aes192gcm=dict(required=False, type='bool'),
    aes256gcm=dict(required=False, type='bool'),
    blowfish=dict(required=False, type='bool'),
    des=dict(required=False, type='bool'),
    cast128=dict(required=False, type='bool'),
    aes_len=dict(required=False, choices=['auto', '128', '192', '256'], type='str'),
    aes128gcm_len=dict(required=False, choices=['auto', '64', '96', '128'], type='str'),
    aes192gcm_len=dict(required=False, choices=['auto', '64', '96', '128'], type='str'),
    aes256gcm_len=dict(required=False, choices=['auto', '64', '96', '128'], type='str'),
    blowfish_len=dict(required=False, choices=['auto', '128', '192', '256'], type='str'),

    # hashes
    md5=dict(required=False, type='bool'),
    sha1=dict(required=False, type='bool'),
    sha256=dict(required=False, type='bool'),
    sha384=dict(required=False, type='bool'),
    sha512=dict(required=False, type='bool'),
    aesxcbc=dict(required=False, type='bool'),

    # misc
    pfsgroup=dict(default='14', choices=['0', '1', '2', '5', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '28', '29', '30'], type='str'),
    lifetime=dict(default=3600, type='int'),
    pinghost=dict(required=False, type='str')
)

IPSEC_P2_REQUIRED_IF = [
    ["state", "present", ["mode"]],

    ["mode", "tunnel", ["local", "remote"]],
    ["mode", "tunnel6", ["local", "remote"]],
    ["mode", "vti", ["local", "remote"]],

    # encryptions
    ["aes", True, ["aes_len"]],
    ["aes128gcm", True, ["aes128gcm_len"]],
    ["aes192gcm", True, ["aes192gcm_len"]],
    ["aes256gcm", True, ["aes256gcm_len"]],
    ["blowfish", True, ["blowfish_len"]],
]


class PFSenseIpsecP2Module(PFSenseModuleBase):
    """ module managing pfsense ipsec phase 2 options and proposals """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseIpsecP2Module, self).__init__(module, pfsense)
        self.name = "pfsense_ipsec_p2"
        self.apply = True
        self.obj = dict()

        if pfsense is None:
            pfsense = PFSenseModule(module)
        self.module = module
        self.pfsense = pfsense
        self.root_elt = self.pfsense.ipsec

        self._phase1 = None
        self.before_elt = None

    ##############################
    # params processing
    #
    def _check_for_duplicate_phase2(self, phase2):
        """ check for another phase2 with same remote and local """
        def strip_phase(phase):
            _phase2 = {}
            if phase.get('localid') is not None:
                _phase2['localid'] = phase['localid']
            if phase.get('remoteid') is not None:
                _phase2['remoteid'] = phase['remoteid']
            return _phase2

        _phase2 = strip_phase(phase2)
        ikeid = self._phase1.find('ikeid').text
        for phase2_elt in self.root_elt:
            if phase2_elt.tag != 'phase2':
                continue

            if phase2_elt.find('ikeid').text != ikeid:
                continue

            if phase2_elt.find('descr').text == phase2['descr']:
                continue

            other_phase2 = self.pfsense.element_to_dict(phase2_elt)
            if _phase2 == strip_phase(other_phase2):
                self.module.fail_json(msg='Phase2 with this Local/Remote networks combination is already defined for this Phase1.')

    def _id_to_phase2(self, name, phase2, address, param_name):
        """ setup ipsec phase2 with address """
        def set_ip_address():
            phase2[name]['type'] = 'address'
            phase2[name]['address'] = address

        def set_ip_network():
            phase2[name]['type'] = 'network'
            (phase2[name]['address'], phase2[name]['netbits']) = self.pfsense.parse_ip_network(address, False)
            phase2[name]['netbits'] = str(phase2[name]['netbits'])
        phase2[name] = dict()

        interface = self._parse_ipsec_interface(address)
        if interface is not None:
            if phase2['mode'] == 'vti':
                msg = 'VTI requires a valid local network or IP address for its endpoint address.'
                self.module.fail_json(msg=msg)
            phase2[name]['type'] = interface
        elif self.pfsense.is_ipv4_address(address):
            if self.params['mode'] == 'tunnel6':
                self.module.fail_json(msg='A valid IPv6 address or network must be specified in {0} with tunnel6.'.format(param_name))
            set_ip_address()
        elif self.pfsense.is_ipv6_address(address):
            if self.params['mode'] == 'tunnel':
                self.module.fail_json(msg='A valid IPv4 address or network must be specified in {0} with tunnel.'.format(param_name))
            set_ip_address()
        elif self.pfsense.is_ipv4_network(address, False):
            if self.params['mode'] == 'tunnel6':
                self.module.fail_json(msg='A valid IPv6 address or network must be specified in {0} with tunnel6.'.format(param_name))
            set_ip_network()
        elif self.pfsense.is_ipv6_network(address, False):
            if self.params['mode'] == 'tunnel':
                self.module.fail_json(msg='A valid IPv4 address or network must be specified in {0} with tunnel.'.format(param_name))
            set_ip_network()
        else:
            self.module.fail_json(msg='A valid IP address, network or interface must be specified in {0}.'.format(param_name))

    def _params_to_obj(self):
        """ return an phase2 dict from module params """
        params = self.params

        obj = dict()
        obj['descr'] = params['descr']
        self.apply = params['apply']

        if params['state'] == 'present':
            obj['mode'] = params['mode']
            if obj['mode'] != 'transport':

                if obj['mode'] == 'vti' and not self.pfsense.is_ip_address(params['remote']):
                    msg = 'VTI requires a valid remote IP address for its endpoint address.'
                    self.module.fail_json(msg=msg)

                self._id_to_phase2('localid', obj, params['local'], 'local')
                self._id_to_phase2('remoteid', obj, params['remote'], 'remote')

                if obj['mode'] != 'vti' and params.get('nat') is not None:
                    self._id_to_phase2('natlocalid', obj, params['nat'], 'nat')

            if params.get('disabled'):
                obj['disabled'] = ''

            obj['protocol'] = params['protocol']
            obj['pfsgroup'] = params['pfsgroup']
            if params.get('lifetime') is not None and params['lifetime'] > 0:
                obj['lifetime'] = str(params['lifetime'])
            else:
                obj['lifetime'] = ''

            if obj.get('pinghost'):
                obj['pinghost'] = params['pinghost']
            else:
                obj['pinghost'] = ''

            self._check_for_duplicate_phase2(obj)

        return obj

    def _parse_ipsec_interface(self, interface):
        """ validate and return an interface param """
        if self.pfsense.is_interface_name(interface):
            return self.pfsense.get_interface_pfsense_by_name(interface)
        elif self.pfsense.is_interface_pfsense(interface):
            return interface

        return None

    def _validate_params(self):
        """ do some extra checks on input parameters """
        def has_one_of(bools):
            for name in bools:
                if params.get(name):
                    return True
            return False

        params = self.params

        # called from ipsec_aggregate
        if params.get('ikeid') is not None:
            self._phase1 = self.pfsense.find_ipsec_phase1(params['ikeid'], 'ikeid')
            if self._phase1 is None:
                self.module.fail_json(msg='No ipsec tunnel with ikeid {0}'.format(params['ikeid']))
        else:
            self._phase1 = self.pfsense.find_ipsec_phase1(params['p1_descr'])
            if self._phase1 is None:
                self.module.fail_json(msg='No ipsec tunnel named {0}'.format(params['p1_descr']))

        if params['state'] == 'present':
            encs = ['aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', 'des', 'cast128']
            if params['protocol'] == 'esp' and not has_one_of(encs):
                self.module.fail_json(msg='At least one encryption algorithm must be selected.')

            hashes = ['md5', 'sha1', 'sha256', 'sha384', 'sha512', 'aesxcbc']
            if not has_one_of(hashes):
                self.module.fail_json(msg='At least one hashing algorithm needs to be selected.')

    ##############################
    # XML processing
    #
    def _copy_and_add_target(self):
        """ create the XML target_elt """
        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self._sync_encryptions(self.target_elt)
        self._sync_hashes(self.target_elt)
        self.root_elt.append(self.target_elt)

    def _copy_and_update_target(self):
        """ update the XML target_elt """
        self.before_elt = deepcopy(self.target_elt)
        before = self.pfsense.element_to_dict(self.target_elt)
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)

        if self._sync_encryptions(self.target_elt):
            changed = True

        if self._sync_hashes(self.target_elt):
            changed = True

        if self._remove_deleted_ipsec_params():
            changed = True

        return (before, changed)

    def _create_target(self):
        """ create the XML target_elt """
        target_elt = self.pfsense.new_element('phase2')
        self.obj['ikeid'] = self._phase1.find('ikeid').text
        self.obj['uniqid'] = self.pfsense.uniqid()
        self.obj['reqid'] = str(self._find_free_reqid())
        return target_elt

    def _find_free_reqid(self):
        """ return first unused reqid """
        reqid = 1
        while True:
            found = False
            for phase2_elt in self.root_elt:
                if phase2_elt.tag != 'phase2':
                    continue
                reqid_elt = phase2_elt.find('reqid')
                if reqid_elt is not None and reqid_elt.text == str(reqid):
                    found = True
                    break

            if not found:
                return reqid
            reqid = reqid + 1

    def _find_target(self):
        """ return ipsec phase2 elt if found """
        ikeid = self._phase1.find('ikeid').text
        for phase2_elt in self.root_elt:
            if phase2_elt.tag != 'phase2':
                continue

            if phase2_elt.find('ikeid').text != ikeid:
                continue

            descr_elt = phase2_elt.find('descr')
            if descr_elt is not None and descr_elt.text == self.obj['descr']:
                return phase2_elt

        return None

    def _remove_deleted_ipsec_params(self):
        """ Remove from phase2 a few deleted params """
        changed = False
        params = ['disabled']

        for param in params:
            if self.pfsense.remove_deleted_param_from_elt(self.target_elt, param, self.obj):
                changed = True

        for param in ['localid', 'remoteid', 'natlocalid']:
            if self._remove_extra_deleted_ipsec_params(param):
                changed = True

        return changed

    def _remove_extra_deleted_ipsec_params(self, name):
        """ Remove from phase2 a few extra deleted params """
        changed = False

        params = ['type', 'address', 'netbits']
        sub_elt = self.target_elt.find(name)
        if sub_elt is not None:
            for param in params:
                if name in self.obj:
                    if self.pfsense.remove_deleted_param_from_elt(sub_elt, param, self.obj[name]):
                        changed = True
                else:
                    if self.pfsense.remove_deleted_param_from_elt(sub_elt, param, dict()):
                        changed = True

            if len(sub_elt) == 0:
                self.target_elt.remove(sub_elt)

        return changed

    def _sync_encryptions(self, phase2_elt):
        """ sync encryptions params """
        def get_encryption(encryptions_elt, name):
            for encryption_elt in encryptions_elt:
                name_elt = encryption_elt.find('name')
                if name_elt is not None and name_elt.text == name:
                    return encryption_elt
            return None

        def sync_encryption(encryptions_elt, name, param_name):
            encryption_elt = get_encryption(encryptions_elt, name)
            if self.params.get(param_name):
                encryption = dict()
                encryption['name'] = name
                if self.params.get(param_name + '_len') is not None:
                    encryption['keylen'] = self.params[param_name + '_len']
                if encryption_elt is None:
                    encryption_elt = self.pfsense.new_element('encryption-algorithm-option')
                    self.pfsense.copy_dict_to_element(encryption, encryption_elt)
                    phase2_elt.append(encryption_elt)
                    return True
                else:
                    old_encryption = self.pfsense.element_to_dict(encryption_elt)
                    if old_encryption != encryption:
                        self.pfsense.copy_dict_to_element(encryption, encryption_elt)
                        return True
            else:
                if encryption_elt is not None:
                    phase2_elt.remove(encryption_elt)
                    return True
            return False

        changed = False
        encryptions_elt = phase2_elt.findall('encryption-algorithm-option')
        if sync_encryption(encryptions_elt, 'aes', 'aes'):
            changed = True
        if sync_encryption(encryptions_elt, 'aes128gcm', 'aes128gcm'):
            changed = True
        if sync_encryption(encryptions_elt, 'aes192gcm', 'aes192gcm'):
            changed = True
        if sync_encryption(encryptions_elt, 'aes256gcm', 'aes256gcm'):
            changed = True
        if sync_encryption(encryptions_elt, 'blowfish', 'blowfish'):
            changed = True
        if sync_encryption(encryptions_elt, '3des', 'des'):
            changed = True
        if sync_encryption(encryptions_elt, 'cast128', 'cast128'):
            changed = True
        return changed

    def _sync_hashes(self, phase2_elt):
        """ sync hashes params """
        def get_hash(hashes_elt, name):
            for hash_elt in hashes_elt:
                if hash_elt.text == name:
                    return hash_elt
            return None

        def sync_hash(hashes_elt, name, param_name):
            if self.params.get(param_name) is not None:
                if get_hash(hashes_elt, name) is None:
                    hash_elt = self.pfsense.new_element('hash-algorithm-option')
                    hash_elt.text = name
                    phase2_elt.append(hash_elt)
                    return True
            else:
                hash_elt = get_hash(hashes_elt, name)
                if hash_elt is not None:
                    phase2_elt.remove(hash_elt)
                    return True
            return False

        changed = False
        hashes_elt = phase2_elt.findall('hash-algorithm-option')
        if sync_hash(hashes_elt, 'hmac_md5', 'md5'):
            changed = True
        if sync_hash(hashes_elt, 'hmac_sha1', 'sha1'):
            changed = True
        if sync_hash(hashes_elt, 'hmac_sha256', 'sha256'):
            changed = True
        if sync_hash(hashes_elt, 'hmac_sha384', 'sha384'):
            changed = True
        if sync_hash(hashes_elt, 'hmac_sha512', 'sha512'):
            changed = True
        if sync_hash(hashes_elt, 'aesxcbc', 'aesxcbc'):
            changed = True
        return changed

    ##############################
    # run
    #
    def _update(self):
        return self.pfsense.phpshell(
            "require_once('vpn.inc');"
            "$ipsec_dynamic_hosts = vpn_ipsec_configure();"
            "$retval = 0;"
            "$retval |= filter_configure();"
            "if ($ipsec_dynamic_hosts >= 0 && is_subsystem_dirty('ipsec'))"
            "   clear_subsystem_dirty('ipsec');"
        )

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}' on '{1}'".format(self.obj['descr'], self.params['p1_descr'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        def log_enc(name):
            log = ''
            log += self.format_cli_field(self.params, name, fvalue=self.fvalue_bool)
            if self.params.get(name) and self.params.get(name + '_len') is not None:
                log += self.format_cli_field(self.params, name + '_len')
            return log
        values = ''
        if before is None:
            values += self.format_cli_field(self.params, 'disabled', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.obj, 'mode')

            values += self.format_cli_field(self.params, 'local')
            values += self.format_cli_field(self.params, 'remote')
            values += self.format_cli_field(self.params, 'nat')

            values += log_enc('aes')
            values += log_enc('aes128gcm')
            values += log_enc('aes192gcm')
            values += log_enc('aes256gcm')
            values += log_enc('blowfish')
            values += log_enc('des')
            values += log_enc('cast128')

            values += self.format_cli_field(self.params, 'md5', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'sha1', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'sha256', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'sha384', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'sha512', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'aesxcbc', fvalue=self.fvalue_bool)

            values += self.format_cli_field(self.params, 'pfsgroup')
            values += self.format_cli_field(self.params, 'lifetime')
            values += self.format_cli_field(self.params, 'pinghost')
        else:
            self._prepare_log_address(before, 'local', 'localid')
            self._prepare_log_address(before, 'nat', 'natlocalid')
            self._prepare_log_address(before, 'remote', 'remoteid')
            self._prepare_log_encryptions(before, self.before_elt)
            self._prepare_log_hashes(before, self.before_elt)

            values += self.format_updated_cli_field(self.obj, before, 'disabled', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'mode', add_comma=(values))

            values += self.format_updated_cli_field(self.params, before, 'local', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'remote', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'nat', add_comma=(values))

            values += self.format_updated_cli_field(self.params, before, 'aes', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'aes_len', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'aes128gcm', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'aes128gcm_len', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'aes192gcm', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'aes192gcm_len', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'aes256gcm', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'aes256gcm_len', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'blowfish', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'blowfish_len', add_comma=(values))
            values += self.format_updated_cli_field(self.params, before, 'des', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'cast128', add_comma=(values), fvalue=self.fvalue_bool)

            values += self.format_updated_cli_field(self.params, before, 'md5', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'sha1', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'sha256', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'sha384', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'sha512', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.params, before, 'aesxcbc', add_comma=(values), fvalue=self.fvalue_bool)

            values += self.format_updated_cli_field(self.obj, before, 'pfsgroup', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'lifetime', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'pinghost', add_comma=(values))
        return values

    def _prepare_log_address(self, before, param, name):
        """ reparse some params for logging """
        if before.get(name) is None or not isinstance(before[name], dict) or before[name].get('type') is None:
            before[param] = None
            return

        if before[name]['type'] == 'address':
            before[param] = before[name]['address']
        elif before[name]['type'] == 'network':
            before[param] = before[name]['address'] + '/' + str(before[name]['netbits'])
        else:
            before[param] = self.pfsense.get_interface_display_name(before[name]['type'])

    @staticmethod
    def _prepare_log_encryptions(before, before_elt):
        """ reparse some params for logging """
        encryptions_elt = before_elt.findall('encryption-algorithm-option')
        for encryption_elt in encryptions_elt:
            name = encryption_elt.find('name').text
            len_elt = encryption_elt.find('keylen')
            if name == '3des':
                name = 'des'
            before[name] = True
            if len_elt is not None:
                before[name + '_len'] = len_elt.text

        encs = ['aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', 'des', 'cast128']
        for enc in encs:
            if enc not in before.keys():
                before[enc] = False
            if enc + '_len' not in before.keys():
                before[enc + '_len'] = None

    @staticmethod
    def _prepare_log_hashes(before, before_elt):
        """ reparse some params for logging """
        hashes_elt = before_elt.findall('hash-algorithm-option')
        for hash_elt in hashes_elt:
            name = hash_elt.text.replace("hmac_", "")
            before[name] = True

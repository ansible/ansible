# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase


IPSEC_PROPOSAL_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    descr=dict(required=False, type='str'),
    encryption=dict(required=True, choices=['aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', '3des', 'cast128'], type='str'),
    key_length=dict(required=False, choices=[64, 96, 128, 192, 256], type='int'),
    hash=dict(required=True, choices=['md5', 'sha1', 'sha256', 'sha384', 'sha512', 'aesxcbc'], type='str'),
    dhgroup=dict(required=True, choices=[1, 2, 5, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 28, 29, 30], type='int'),
    apply=dict(default=True, type='bool'),
)

IPSEC_PROPOSAL_REQUIRED_IF = [
    ["encryption", "aes", ["key_length"]],
    ["encryption", "aes128-gcm", ["key_length"]],
    ["encryption", "aes192-gcm", ["key_length"]],
    ["encryption", "aes256-gcm", ["key_length"]],
    ["encryption", "blowfish", ["key_length"]],
]


class PFSenseIpsecProposalModule(PFSenseModuleBase):
    """ module managing pfsense ipsec phase 1 proposals """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseIpsecProposalModule, self).__init__(module, pfsense)
        self.name = "pfsense_ipsec_proposal"
        self.root_elt = None
        self.obj = dict()
        self.apply = True

        self.ipsec = self.pfsense.ipsec
        self._phase1 = None

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        obj['encryption-algorithm'] = dict()
        obj['encryption-algorithm']['name'] = params['encryption']
        if params.get('key_length') is not None:
            obj['encryption-algorithm']['keylen'] = str(params['key_length'])
        else:
            obj['encryption-algorithm']['keylen'] = ''
        obj['hash-algorithm'] = params['hash']
        obj['dhgroup'] = str(params['dhgroup'])

        self.apply = params['apply']

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        key_length = dict()
        key_length['aes'] = ['128', '192', '256']
        key_length['aes192gcm'] = ['64', '96', '128']
        key_length['aes128gcm'] = ['64', '96', '128']
        key_length['aes256gcm'] = ['64', '96', '128']
        key_length['blowfish'] = ['128', '192', '256']
        if params['encryption'] in key_length.keys() and str(params['key_length']) not in key_length[params['encryption']]:
            msg = 'key_length for encryption {0} must be one of: {1}.'.format(params['encryption'], ', '.join(key_length[params['encryption']]))
            self.module.fail_json(msg=msg)

        # called from ipsec_aggregate
        if params.get('ikeid') is not None:
            self._phase1 = self.pfsense.find_ipsec_phase1(params['ikeid'], 'ikeid')
            if self._phase1 is None:
                self.module.fail_json(msg='No ipsec tunnel with ikeid {0}'.format(params['ikeid']))
        else:
            self._phase1 = self.pfsense.find_ipsec_phase1(params['descr'])
            if self._phase1 is None:
                self.module.fail_json(msg='No ipsec tunnel named {0}'.format(params['descr']))

        self.root_elt = self._phase1.find('encryption')
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('encryption')
            self._phase1.append(self.root_elt)

        if params['encryption'] in ['aes128gcm', 'aes192gcm', 'aes256gcm']:
            iketype_elt = self._phase1.find('iketype')
            if iketype_elt is not None and iketype_elt.text != 'ikev2':
                self.module.fail_json(msg='Encryption Algorithm AES-GCM can only be used with IKEv2')

    ##############################
    # XML processing
    #
    @staticmethod
    def _copy_and_update_target():
        """ update the XML target_elt """
        return (None, False)

    def _create_target(self):
        """ create the XML target_elt """
        return self.pfsense.new_element('item')

    def _find_target(self):
        """ find the XML target_elt """
        items_elt = self.root_elt.findall('item')
        for item in items_elt:
            existing = self.pfsense.element_to_dict(item)
            if existing == self.obj:
                return item
        return None

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
        return "'{0}'".format(self.params['descr'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        values += self.format_cli_field(self.params, 'encryption')
        values += self.format_cli_field(self.params, 'key_length')
        values += self.format_cli_field(self.obj, 'hash-algorithm', fname='hash')
        values += self.format_cli_field(self.obj, 'dhgroup')
        return values

    def _log_fields_delete(self):
        """ generate pseudo-CLI command fields parameters to delete an obj """
        return self._log_fields()

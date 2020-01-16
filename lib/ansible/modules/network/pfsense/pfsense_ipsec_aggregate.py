#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_ipsec_aggregate
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage multiple pfSense ipsec tunnels, phases 1, phases 2 and proposals
description:
  - Manage multiple pfSense ipsec tunnels, phases 1, phases 2 and proposals
notes:
  - aggregated_* use the same options definitions than pfsense corresponding module
options:
  aggregated_ipsecs:
    description: Dict of ipsec tunnels and phase 1 options to apply on the target
    required: False
    type: list
    suboptions:
      iketype:
        description: Internet Key Exchange protocol version to be used. Auto uses IKEv2 when initiator, and accepts either IKEv1 or IKEv2 as responder.
        required: false
        choices: [ 'ikev1', 'ikev2', 'auto' ]
        type: str
      protocol:
        description: IP family
        default: 'inet'
        choices: [ 'inet', 'inet6', 'both' ]
        type: str
      interface:
        description: Interface for the local endpoint of this phase1 entry.
        required: false
        type: str
      remote_gateway:
        description: Public IP address or host name of the remote gateway.
        required: false
        type: str
      disabled:
        description: Set this option to disable this phase1 without removing it from the list.
        required: false
        type: bool
      authentication_method:
        description: Authenticatin method. Must match the setting chosen on the remote side.
        choices: [ 'pre_shared_key', 'rsasig' ]
        type: str
      mode:
        description: Negotiation mode. Aggressive is more flexible, but less secure. Only for IkeV1 or Auto.
        choices: [ 'main', 'aggressive' ]
        type: str
      myid_type:
        description: Local identifier type.
        default: 'myaddress'
        choices: [ 'myaddress', 'address', 'fqdn', 'user_fqdn', 'asn1dn', 'keyid tag', 'dyn_dns' ]
        type: str
      myid_data:
        description: Local identifier value.
        required: false
        type: str
      peerid_type:
        description: Remote identifier type.
        default: 'peeraddress'
        choices: [ 'any', 'peeraddress', 'address', 'fqdn', 'user_fqdn', 'asn1dn', 'keyid tag' ]
        type: str
      peerid_data:
        description: Remote identifier value.
        required: false
        type: str
      certificate:
        description: a certificate previously configured
        required: false
        type: str
      certificate_authority:
        description: a certificate authority previously configured
        required: false
        type: str
      preshared_key:
        description: This key must match on both peers.
        required: false
        type: str
      lifetime:
        description: The lifetime defines how often the connection will be rekeyed, in seconds.
        default: 28800
        type: int
      disable_rekey:
        description: Disables renegotiation when a connection is about to expire.
        default: false
        type: bool
      margintime:
        description: How long before connection expiry or keying-channel expiry should attempt to negotiate a replacement begin.
        required: false
        type: int
      responderonly:
        description: Enable this option to never initiate this connection from this side, only respond to incoming requests.
        default: false
        type: bool
      disable_reauth:
        description: (IKEv2 only) Whether rekeying of an IKE_SA should also reauthenticate the peer. In IKEv1, reauthentication is always done.
        default: false
        type: bool
      mobike:
        description: (IKEv2 only) Set this option to control the use of MOBIKE
        default: 'off'
        choices: [ 'on', 'off' ]
        type: str
      splitconn:
        description: (IKEv2 only) Enable this to split connection entries with multiple phase 2 configurations
        default: false
        type: bool
      nat_traversal:
        description:
          Set this option to enable the use of NAT-T (i.e. the encapsulation of ESP in UDP packets) if needed,
          which can help with clients that are behind restrictive firewalls.
        default: 'on'
        choices: [ 'on', 'force' ]
        type: str
      enable_dpd:
        description: Enable dead peer detection
        default: True
        type: bool
      dpd_delay:
        description: Delay between requesting peer acknowledgement.
        default: 10
        type: int
      dpd_maxfail:
        description: Number of consecutive failures allowed before disconnect.
        default: 5
        type: int
      descr:
        description: The description of the ipsec tunnel
        default: null
        required: True
        type: str
      state:
        description: State in which to leave the ipsec tunnel
        choices: [ "present", "absent" ]
        default: present
        type: str
      apply:
        description: Apply VPN configuration on target pfSense
        default: True
        type: bool
  aggregated_ipsec_proposals:
    description: Dict of ipsec proposals to apply on the target
    required: False
    type: list
    suboptions:
      encryption:
        description:
          Encryption algorithm. aes128gcm, aes192gcm and aes256gcm can only be used with IKEv2 tunnels.
          Blowfish, 3DES and CAST128 provide weak security and should be avoided.
        required: True
        choices: [ 'aes', 'aes128gcm', 'aes192gcm', 'aes256gcm', 'blowfish', '3des', 'cast128' ]
        type: str
      key_length:
        description: Encryption key length
        required: False
        choices: [ 64, 96, 128, 192, 256 ]
        type: int
      hash:
        description: Hash algorithm. MD5 and SHA1 provide weak security and should be avoided.
        required: True
        choices: [ 'md5', 'sha1', 'sha256', 'sha384', 'sha512', 'aesxcbc' ]
        type: str
      dhgroup:
        description: DH group. DH groups 1, 2, 22, 23, and 24 provide weak security and should be avoided.
        required: True
        choices: [ 1, 2, 5, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 28, 29, 30 ]
        type: int
      descr:
        description: The description of the ipsec tunnel on which to create/delete the proposal.
        default: null
        type: str
      state:
        description: State in which to leave the ipsec proposal.
        choices: [ "present", "absent" ]
        default: present
        type: str
      apply:
        description: Apply VPN configuration on target pfSense
        default: True
        type: bool
  aggregated_ipsec_p2s:
    description: Dict of ipsec tunnels phase 2 options to apply on the target
    required: False
    type: list
    suboptions:
      disabled:
        description: Set this option to disable this phase2 without removing it from the list.
        required: false
        type: bool
      mode:
        description: Method for managing ipsec traffic
        required: False
        choices: [ 'tunnel', 'tunnel6', 'transport', 'vti' ]
        type: str
      local:
        description: Local network component of this IPsec security association.
        required: False
        type: str
      nat:
        description: If NAT/BINAT is required on the local network specify the address to be translated
        required: False
        type: str
      remote:
        description: Remote network component of this IPsec security association.
        required: False
        type: str
      protocol:
        description: Encapsulating Security Payload (ESP) is encryption, Authentication Header (AH) is authentication only.
        default: 'esp'
        choices: [ 'esp', 'ah' ]
        type: str
      aes:
        description: Set this option to enable AES encryption.
        required: false
        type: bool
      aes_len:
        description: AES encryption key length
        required: False
        choices: [ 'auto', '128', '192', '256' ]
        type: str
      aes128gcm:
        description: Set this option to enable AES128-GCM encryption.
        required: false
        type: bool
      aes128gcm_len:
        description: AES128-GCM encryption key length
        required: False
        choices: [ 'auto', '64', '96', '128' ]
        type: str
      aes192gcm:
        description: Set this option to enable AES192-GCM encryption.
        required: false
        type: bool
      aes192gcm_len:
        description: AES192-GCM encryption key length
        required: False
        choices: [ 'auto', '64', '96', '128' ]
        type: str
      aes256gcm:
        description: Set this option to enable AES256-GCM encryption.
        required: false
        type: bool
      aes256gcm_len:
        description: AES256-GCM encryption key length
        required: False
        choices: [ 'auto', '64', '96', '128' ]
        type: str
      blowfish:
        description: Set this option to enable Blowfish encryption.
        required: false
        type: bool
      blowfish_len:
        description: AES encryption key length
        required: False
        choices: [ 'auto', '128', '192', '256' ]
        type: str
      des:
        description: Set this option to enable 3DES encryption.
        required: false
        type: bool
      cast128:
        description: Set this option to enable CAST128 encryption.
        required: false
        type: bool
      md5:
        description: Set this option to enable MD5 hashing.
        required: false
        type: bool
      sha1:
        description: Set this option to enable SHA1 hashing.
        required: false
        type: bool
      sha256:
        description: Set this option to enable SHA256 hashing.
        required: false
        type: bool
      sha384:
        description: Set this option to enable SHA384 hashing.
        required: false
        type: bool
      sha512:
        description: Set this option to enable SHA512 hashing.
        required: false
        type: bool
      aesxcbc:
        description: Set this option to enable AES-XCBC hashing.
        required: false
        type: bool
      pfsgroup:
        description: PFS key group, 0 for off. DH groups 1, 2, 22, 23, and 24 provide weak security and should be avoided.
        default: '14'
        choices: [ '0', '1', '2', '5', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '28', '29', '30' ]
        type: str
      lifetime:
        description: Specifies how often the connection must be rekeyed, in seconds
        default: 3600
        type: int
      pinghost:
        description: Automatically ping host
        required: False
        type: str
      descr:
        description: The description of the ipsec tunnel phase2
        required: True
        type: str
      p1_descr:
        description: The description of the ipsec tunnel
        required: true
        type: str
      state:
        description: State in which to leave the ipsec tunnel phase2
        choices: [ "present", "absent" ]
        default: present
        type: str
      apply:
        description: Apply VPN configuration on target pfSense
        default: True
        type: bool
  purge_ipsecs:
    description: delete all the ipsec tunnels that are not defined into aggregated_ipsecs
    required: False
    default: False
    type: bool
  purge_ipsec_proposals:
    description: delete all the phase1 proposals that are not defined into aggregated_ipsec_proposals
    required: False
    default: False
    type: bool
  purge_ipsec_p2s:
    description: delete all the phase2 that are not defined into aggregated_ipsec_p2s
    required: False
    default: False
    type: bool
  apply:
    description: Apply VPN configuration on target pfSense
    default: True
    type: bool
"""

EXAMPLES = """
- name: "Setup two tunnels with two proposals and and two phase 2 each, and delete everything else"
  pfsense_ipsec_aggregate:
    purge_ipsecs: true
    purge_ipsec_proposals: true
    purge_ipsec_p2s: true
    aggregated_ipsecs:
      - { descr: t1, interface: wan, remote_gateway: 1.3.3.1, iketype: ikev2, authentication_method: pre_shared_key, preshared_key: azerty123 }
      - { descr: t2, interface: wan, remote_gateway: 1.3.4.1, iketype: ikev2, authentication_method: pre_shared_key, preshared_key: qwerty123 }
    aggregated_ipsec_proposals:
      - { descr: t1, encryption: aes, key_length: 128, hash: md5, dhgroup: 14}
      - { descr: t2, encryption: 3des, hash: sha512, dhgroup: 14}
    aggregated_ipsec_p2s:
      - { descr: t1_p2_1, p1_descr: t1, mode: tunnel, local: 1.2.3.4/24, remote: 10.20.30.40/24, aes: True, aes_len: auto, sha256: True }
      - { descr: t1_p2_2, p1_descr: t1, mode: tunnel, local: 1.2.3.4/24, remote: 10.20.30.50/24, aes: True, aes_len: auto, sha256: True }
      - { descr: t2_p2_1, p1_descr: t2, mode: tunnel, local: 1.2.3.4/24, remote: 10.20.40.40/24, aes: True, aes_len: auto, sha256: True }
      - { descr: t2_p2_2, p1_descr: t2, mode: tunnel, local: 1.2.3.4/24, remote: 10.20.40.50/24, aes: True, aes_len: auto, sha256: True }
"""

RETURN = """
result_ipsecs:
    description: the set of separators commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create ipsec 'test_tunnel', iketype='ikev2', protocol='inet', interface='wan', remote_gateway='1.2.3.4', ...", "delete ipsec 'test_tunnel'"]
result_ipsec_proposals:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: [
        "create ipsec_proposal on 'test_tunnel', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'",
        "delete ipsec_proposal on 'test_tunnel', encryption='aes128gcm', key_length=128, hash='sha256', dhgroup='14'",
    ]
result_ipsec_p2s:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create ipsec_p2 'test_p2' on 'test_tunnel', disabled='False', mode='vti', local='1.2.3.1', ...", "delete ipsec_p2 'test_p2' on 'test_tunnel'"]
"""

from ansible.module_utils.network.pfsense.pfsense import PFSenseModule
from ansible.module_utils.network.pfsense.ipsec import PFSenseIpsecModule, IPSEC_ARGUMENT_SPEC, IPSEC_REQUIRED_IF
from ansible.module_utils.network.pfsense.ipsec_proposal import PFSenseIpsecProposalModule
from ansible.module_utils.network.pfsense.ipsec_proposal import IPSEC_PROPOSAL_ARGUMENT_SPEC
from ansible.module_utils.network.pfsense.ipsec_proposal import IPSEC_PROPOSAL_REQUIRED_IF
from ansible.module_utils.network.pfsense.ipsec_p2 import PFSenseIpsecP2Module
from ansible.module_utils.network.pfsense.ipsec_p2 import IPSEC_P2_ARGUMENT_SPEC
from ansible.module_utils.network.pfsense.ipsec_p2 import IPSEC_P2_REQUIRED_IF

from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy


class PFSenseModuleIpsecAggregate(object):
    """ module managing pfsense aggregated ipsec tunnels, phases 1, phases 2 and proposals """

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.pfsense_ipsec = PFSenseIpsecModule(module, self.pfsense)
        self.pfsense_ipsec_proposal = PFSenseIpsecProposalModule(module, self.pfsense)
        self.pfsense_ipsec_p2 = PFSenseIpsecP2Module(module, self.pfsense)

    def _update(self):
        if self.pfsense_ipsec.result['changed'] or self.pfsense_ipsec_proposal.result['changed'] or self.pfsense_ipsec_p2.result['changed']:
            return self.pfsense.phpshell(
                "require_once('vpn.inc');"
                "$ipsec_dynamic_hosts = vpn_ipsec_configure();"
                "$retval = 0;"
                "$retval |= filter_configure();"
                "if ($ipsec_dynamic_hosts >= 0 && is_subsystem_dirty('ipsec'))"
                "   clear_subsystem_dirty('ipsec');"
            )

        return ('', '', '')

    @staticmethod
    def want_ipsec(ipsec_elt, ipsecs):
        """ return True if we want to keep ipsec_elt """
        descr = ipsec_elt.find('descr')

        if descr is None:
            return True

        for ipsec in ipsecs:
            if ipsec['state'] == 'absent':
                continue
            if ipsec['descr'] == descr.text:
                return True
        return False

    def proposal_elt_to_params(self, ipsec_elt, proposal_elt):
        """ return the pfsense_ipsec_proposal params corresponding the proposal_elt """
        params = {}
        proposal = self.pfsense.element_to_dict(proposal_elt)
        params['encryption'] = proposal['encryption-algorithm']['name']
        params['key_length'] = proposal['encryption-algorithm'].get('keylen')
        if params['key_length'] is not None:
            if params['key_length'] == '':
                params['key_length'] = None
            else:
                params['key_length'] = int(params['key_length'])
        params['hash'] = proposal['hash-algorithm']
        params['dhgroup'] = int(proposal['dhgroup'])
        descr_elt = ipsec_elt.find('descr')
        if descr_elt is None:
            params['descr'] = ''
        else:
            params['descr'] = descr_elt.text

        return params

    def want_ipsec_proposal(self, ipsec_elt, proposal_elt, proposals):
        """ return True if we want to keep proposal_elt """
        params_from_elt = self.proposal_elt_to_params(ipsec_elt, proposal_elt)
        params_from_elt['state'] = 'present'

        if proposals is not None:
            for proposal in proposals:
                _proposal = deepcopy(proposal)
                _proposal.pop('apply', None)
                if params_from_elt == _proposal:
                    return True

        return False

    def want_ipsec_phase2(self, phase2_elt, phases2):
        """ return True if we want to keep proposal_elt """
        ikeid_elt = phase2_elt.find('ikeid')
        descr = phase2_elt.find('descr')

        if descr is None or ikeid_elt is None:
            return True

        phase1_elt = self.pfsense.find_ipsec_phase1(ikeid_elt.text, 'ikeid')
        if phase1_elt is None:
            return True
        phase1_descr_elt = phase1_elt.find('descr')
        if phase1_descr_elt is None:
            return True
        p1_descr = phase1_descr_elt.text

        if phases2 is not None:
            for phase2 in phases2:
                if phase2['state'] == 'absent':
                    continue
                if phase2['descr'] == descr.text and phase2['p1_descr'] == p1_descr:
                    return True
        return False

    def run_ipsecs(self):
        """ process input params to add/update/delete all ipsecs tunnels """
        want = self.module.params['aggregated_ipsecs']

        # processing aggregated parameter
        if want is not None:
            for param in want:
                self.pfsense_ipsec.run(param)

        # delete every other if required
        if self.module.params['purge_ipsecs']:
            todel = []
            for ipsec_elt in self.pfsense_ipsec.root_elt:
                if ipsec_elt.tag != 'phase1':
                    continue
                if not self.want_ipsec(ipsec_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['apply'] = False
                    params['descr'] = ipsec_elt.find('descr').text
                    params['ikeid'] = ipsec_elt.find('ikeid').text
                    todel.append(params)

            for params in todel:
                self.pfsense_ipsec.run(params)

    def run_ipsec_proposals(self):
        """ process input params to add/update/delete all ipsecs tunnels """
        want = self.module.params['aggregated_ipsec_proposals']

        # processing aggregated parameter
        if want is not None:
            for param in want:
                self.pfsense_ipsec_proposal.run(param)

        # delete every other if required
        if self.module.params['purge_ipsec_proposals']:
            todel = []
            for ipsec_elt in self.pfsense_ipsec_proposal.ipsec:
                if ipsec_elt.tag != 'phase1':
                    continue

                encryption_elt = ipsec_elt.find('encryption')
                if encryption_elt is None:
                    continue

                items_elt = encryption_elt.findall('item')
                for proposal_elt in items_elt:
                    if not self.want_ipsec_proposal(ipsec_elt, proposal_elt, want):
                        params = self.proposal_elt_to_params(ipsec_elt, proposal_elt)
                        params['state'] = 'absent'
                        params['apply'] = False
                        params['descr'] = ipsec_elt.find('descr').text
                        params['ikeid'] = ipsec_elt.find('ikeid').text
                        todel.append(params)

            for params in todel:
                self.pfsense_ipsec_proposal.run(params)

    def run_ipsec_p2s(self):
        """ process input params to add/update/delete all ipsecs tunnels """
        want = self.module.params['aggregated_ipsec_p2s']

        # processing aggregated parameter
        if want is not None:
            for param in want:
                self.pfsense_ipsec_p2.run(param)

        # delete every other if required
        if self.module.params['purge_ipsec_p2s']:
            todel = []
            for phase2_elt in self.pfsense_ipsec_p2.root_elt:
                if phase2_elt.tag != 'phase2':
                    continue
                if not self.want_ipsec_phase2(phase2_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['apply'] = False
                    params['descr'] = phase2_elt.find('descr').text
                    params['p1_descr'] = self.pfsense.find_ipsec_phase1(phase2_elt.find('ikeid').text, 'ikeid').find('descr').text
                    params['ikeid'] = phase2_elt.find('ikeid').text
                    todel.append(params)

            for params in todel:
                self.pfsense_ipsec_p2.run(params)

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        changed = self.pfsense_ipsec.result['changed'] or self.pfsense_ipsec_proposal.result['changed'] or self.pfsense_ipsec_p2.result['changed']

        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr='aggregated change')
            if self.module.params['apply']:
                (dummy, stdout, stderr) = self._update()

        result = {}
        result['result_ipsecs'] = self.pfsense_ipsec.result['commands']
        result['result_ipsec_proposals'] = self.pfsense_ipsec_proposal.result['commands']
        result['result_ipsec_p2s'] = self.pfsense_ipsec_p2.result['commands']
        result['changed'] = changed
        result['stdout'] = stdout
        result['stderr'] = stderr
        self.module.exit_json(**result)


def main():
    argument_spec = dict(
        aggregated_ipsecs=dict(type='list', elements='dict', options=IPSEC_ARGUMENT_SPEC, required_if=IPSEC_REQUIRED_IF),
        aggregated_ipsec_proposals=dict(type='list', elements='dict', options=IPSEC_PROPOSAL_ARGUMENT_SPEC, required_if=IPSEC_PROPOSAL_REQUIRED_IF),
        aggregated_ipsec_p2s=dict(type='list', elements='dict', options=IPSEC_P2_ARGUMENT_SPEC, required_if=IPSEC_P2_REQUIRED_IF),
        purge_ipsecs=dict(default=False, type='bool'),
        purge_ipsec_proposals=dict(default=False, type='bool'),
        purge_ipsec_p2s=dict(default=False, type='bool'),
        apply=dict(default=True, type='bool'),
    )

    required_one_of = [['aggregated_ipsecs', 'aggregated_ipsec_proposals', 'aggregated_ipsec_p2s']]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        supports_check_mode=True)

    pfmodule = PFSenseModuleIpsecAggregate(module)

    pfmodule.run_ipsecs()
    pfmodule.run_ipsec_proposals()
    pfmodule.run_ipsec_p2s()

    pfmodule.commit_changes()


if __name__ == '__main__':
    main()

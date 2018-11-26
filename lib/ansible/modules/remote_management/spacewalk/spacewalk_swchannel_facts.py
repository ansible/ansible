#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Copyright: (c) 2018, Davide Blasi (@davegarath)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: spacewalk_swchannel_facts
short_description: Gather facts about all channels in spacewalk
description:
  - "Gather facts about all channels in spacewalk"
version_added: "2.8"
author:
  - Davide Blasi (@davegarath)
extends_documentation_fragment: spacewalk.documentation
'''

EXAMPLES = r'''
- name: Get all channels in spacewalk
  spacewalk_swchannel_facts:
      url: "{{ spacewalk_url_api }}"
      login: "{{ spacewalk_login }}"
      password: "{{ spacewalk_passowrd }}"
  delegate_to: localhost
  register: channels

- debug: var=channels
'''

RETURN = r'''
channels_facts:
  description: Provides all spacewalk channels in ansible_facts
  type: complex
  returned: succes
  contains:
    id:
      description: Identification of the channel
      type: int
      sample: 101
    label:
      description: The label name of the channel
      type: string
      sample: "centos5-centos5-x86_64"
    name:
      description: The channel name
      type: string
      sample: "CentOS 5 Alt.ru (x86_64)"
    summary:
      description: The summary desctription of the channel
      type: string
      sample: "CentOS 5 Alt.ru (x86_64)"
    arch_label:
      description: The architecture label of the channel
      type: string
      sample: "channel-x86_64"
    arch_name:
      description: The architecture name of the channel
      type: string
      sample: "x86_64"
    parent_channel_label:
      description: The label of the parent channel. Default empty
      type: string
      sample: "centos5-x86_64"
    checksum_label:
      description: The checksum Type. Could be 'sha1'(Default) 'sha256', 'sha512'
      type: string
      sample: "sha1"
    gpg_key_url:
      description: The GPG key URL of the channel
      type: string
      sample: "http://centos.alt.ru/repository/centos/RPM-GPG-KEY-CentALT"
    gpg_key_id:
      description: The GPG key ID of the channel
      type: string
      sample: "E8562897"
    gpg_key_fp:
      description: The GPG key Fingerprint of the channel
      type: string
      sample: "473D 66D5 2122 71FD 51CC  17B1 A8A4 47DC E856 2897"
    maintainer_name:
      description: Channel maintainer name
      type: string
      sample: ""
    maintainer_email:
      description: Channel maintainer email
      type: string
      sample: ""
    maintainer_phone:
      description: Channel maintainer phone
      type: string
      sample: ""
    clone_original:
      description: The original repository from this channel has been created
      type: string
      sample: ""
    contentSources:
      description: List of repositories associated to this channel
      type: complex
      contains:
        id:
          description: The id of reposity
          type: int
          sample: 521
        label:
          description: The label of reposity associated to the channel
          type: string
          sample: "External yum repo - CentOS 5 Alt.ru (x86_64)"
        sourceUrl:
          description: The URL of repository
          type: string
          sample: "http://centos.alt.ru/repository/centos/5/x86_64/"
        type:
          description: The repository type (could be yum(Defaul), dnf or deb)
          type: string
          sample: "yum"
    description:
      description: Description of the channel
      type: string
      sample: ""
    last_modified:
      description: Datetime of last modify to the channel
      type: string
      sample: "20181124T08:00:00"
    end_of_life:
      description: Datetime when the channel will be in EOL
      type: string
      sample: ""
    yumrepo_last_sync:
      description: Datetime of the last sync of the repositories
      type: string
      sample: "20181124T08:00:05"
    packages:
      description: Number of packages handled by the channel
      type: int
      sample: 0
    provider_name:
      description: The organization where the channel lives
      type: string
      sample: "Spacewalk Default Organization"
    systems:
      description: Number of sytem subsribed to the channel
      type: int
      sample: 0
    support_policy:
      description:
      type: string
      sample: ""
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.spacewalk import spacewalk_argument_spec, Channel


def main():
    argument_spec = spacewalk_argument_spec()
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    channel = Channel(module)
    ansible_facts = channel.get_all_channels()
    module.exit_json(changed=False, ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()

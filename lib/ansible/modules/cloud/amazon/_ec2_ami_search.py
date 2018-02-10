#!/usr/bin/python
#
# (c) 2013, Nimbis Services
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_ami_search
short_description: Retrieve AWS AMI information for a given operating system.
deprecated:
  removed_in: "2.2"
  why: Various AWS modules have been combined and replaced with M(ec2_ami_facts).
  alternative: Use M(ec2_ami_find) instead.
version_added: "1.6"
description:
  - Look up the most recent AMI on AWS for a given operating system.
  - Returns C(ami), C(aki), C(ari), C(serial), C(tag)
  - If there is no AKI or ARI associated with an image, these will be C(null).
  - Only supports images from cloud-images.ubuntu.com
  - 'Example output: C({"ami": "ami-69f5a900", "changed": false, "aki": "aki-88aa75e1", "tag": "release", "ari": null, "serial": "20131024"})'
options:
  distro:
    description: Linux distribution (e.g., C(ubuntu))
    required: true
    choices: ["ubuntu"]
  release:
    description: short name of the release (e.g., C(precise))
    required: true
  stream:
    description: Type of release.
    required: false
    default: "server"
    choices: ["server", "desktop"]
  store:
    description: Back-end store for instance
    required: false
    default: "ebs"
    choices: ["ebs", "ebs-io1", "ebs-ssd", "instance-store"]
  arch:
    description: CPU architecture
    required: false
    default: "amd64"
    choices: ["i386", "amd64"]
  region:
    description: EC2 region
    required: false
    default: us-east-1
    choices: ["ap-northeast-1", "ap-southeast-1", "ap-northeast-2",
              "ap-southeast-2", "ca-central-1", "eu-central-1", "eu-west-1",
              "eu-west-2", "sa-east-1", "us-east-1", "us-east-2", "us-west-1",
              "us-west-2", "us-gov-west-1"]
  virt:
    description: virutalization type
    required: false
    default: paravirtual
    choices: ["paravirtual", "hvm"]

author: "Ansible Core Team (deprecated)"
'''

EXAMPLES = '''
- name: Launch an Ubuntu 12.04 (Precise Pangolin) EC2 instance
  hosts: 127.0.0.1
  connection: local
  tasks:
  - name: Get the Ubuntu precise AMI
    ec2_ami_search:
      distro: ubuntu
      release: precise
      region: us-west-1
      store: instance-store
    register: ubuntu_image

  - name: Start the EC2 instance
    ec2:
      image: "{{ ubuntu_image.ami }}"
      instance_type: m1.small
      key_name: mykey
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()

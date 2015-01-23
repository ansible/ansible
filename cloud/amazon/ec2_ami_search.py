#!/usr/bin/python
#
# (c) 2013, Nimbis Services
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_ami_search
short_description: Retrieve AWS AMI information for a given operating system.
version_added: "1.6"
description:
  - Look up the most recent AMI on AWS for a given operating system.
  - Returns C(ami), C(aki), C(ari), C(serial), C(tag)
  - If there is no AKI or ARI associated with an image, these will be C(null).
  - Only supports images from cloud-images.ubuntu.com
  - 'Example output: C({"ami": "ami-69f5a900", "changed": false, "aki": "aki-88aa75e1", "tag": "release", "ari": null, "serial": "20131024"})'
version_added: "1.6"
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
    choices: ["ap-northeast-1", "ap-southeast-1", "ap-southeast-2",
              "eu-central-1", "eu-west-1", "sa-east-1", "us-east-1",
              "us-west-1", "us-west-2", "us-gov-west-1"]
  virt:
    description: virutalization type
    required: false
    default: paravirtual
    choices: ["paravirtual", "hvm"]

author: Lorin Hochstein
'''

EXAMPLES = '''
- name: Launch an Ubuntu 12.04 (Precise Pangolin) EC2 instance
  hosts: 127.0.0.1
  connection: local
  tasks:
  - name: Get the Ubuntu precise AMI
    ec2_ami_search: distro=ubuntu release=precise region=us-west-1 store=instance-store
    register: ubuntu_image
  - name: Start the EC2 instance
    ec2: image={{ ubuntu_image.ami }} instance_type=m1.small key_name=mykey
'''

import csv
import json
import urllib2
import urlparse

SUPPORTED_DISTROS = ['ubuntu']

AWS_REGIONS = ['ap-northeast-1',
               'ap-southeast-1',
               'ap-southeast-2',
               'eu-central-1',
               'eu-west-1',
               'sa-east-1',
               'us-east-1',
               'us-west-1',
               'us-west-2',
               "us-gov-west-1"]


def get_url(module, url):
    """ Get url and return response """
    try:
        r = urllib2.urlopen(url)
    except (urllib2.HTTPError, urllib2.URLError), e:
        code = getattr(e, 'code', -1)
        module.fail_json(msg="Request failed: %s" % str(e), status_code=code)
    return r


def ubuntu(module):
    """ Get the ami for ubuntu """

    release = module.params['release']
    stream = module.params['stream']
    store = module.params['store']
    arch = module.params['arch']
    region = module.params['region']
    virt = module.params['virt']

    url = get_ubuntu_url(release, stream)

    req = get_url(module, url)
    reader = csv.reader(req, delimiter='\t')
    try:
        ami, aki, ari, tag, serial = lookup_ubuntu_ami(reader, release, stream,
            store, arch, region, virt)
        module.exit_json(changed=False, ami=ami, aki=aki, ari=ari, tag=tag,
            serial=serial)
    except KeyError:
        module.fail_json(msg="No matching AMI found")


def lookup_ubuntu_ami(table, release, stream, store, arch, region, virt):
    """ Look up the Ubuntu AMI that matches query given a table of AMIs

        table: an iterable that returns a row of
               (release, stream, tag, serial, region, ami, aki, ari, virt)
        release: ubuntu release name
        stream: 'server' or 'desktop'
        store: 'ebs', 'ebs-io1', 'ebs-ssd' or 'instance-store'
        arch: 'i386' or 'amd64'
        region: EC2 region
        virt: 'paravirtual' or 'hvm'

        Returns (ami, aki, ari, tag, serial)"""
    expected = (release, stream, store, arch, region, virt)

    for row in table:
        (actual_release, actual_stream, tag, serial,
            actual_store, actual_arch, actual_region, ami, aki, ari,
            actual_virt) = row
        actual = (actual_release, actual_stream, actual_store, actual_arch,
            actual_region, actual_virt)
        if actual == expected:
            # aki and ari are sometimes blank
            if aki == '':
                aki = None
            if ari == '':
                ari = None
            return (ami, aki, ari, tag, serial)

    raise KeyError()


def get_ubuntu_url(release, stream):
    url = "https://cloud-images.ubuntu.com/query/%s/%s/released.current.txt"
    return url % (release, stream)


def main():
    arg_spec = dict(
        distro=dict(required=True, choices=SUPPORTED_DISTROS),
        release=dict(required=True),
        stream=dict(required=False, default='server',
            choices=['desktop', 'server']),
        store=dict(required=False, default='ebs',
            choices=['ebs', 'ebs-io1', 'ebs-ssd', 'instance-store']),
        arch=dict(required=False, default='amd64',
            choices=['i386', 'amd64']),
        region=dict(required=False, default='us-east-1', choices=AWS_REGIONS),
        virt=dict(required=False, default='paravirtual',
            choices=['paravirtual', 'hvm'])
    )
    module = AnsibleModule(argument_spec=arg_spec)
    distro = module.params['distro']

    if distro == 'ubuntu':
        ubuntu(module)
    else:
        module.fail_json(msg="Unsupported distro: %s" % distro)



# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

if __name__ == '__main__':
    main()

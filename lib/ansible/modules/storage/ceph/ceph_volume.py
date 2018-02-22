#!/usr/bin/python

#
# Copyright (c) 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_volume

short_description: Create ceph OSDs with ceph-volume

version_added: "2.6"

description:
    - Using the ceph-volume utility available in Ceph this module
      can be used to create ceph OSDs that are backed by logical volumes.
    - Only available in ceph versions luminous or greater.

options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    subcommand:
        description:
            - The ceph-volume subcommand to use.
        required: false
        default: lvm
        choices: ['lvm']
    objectstore:
        description:
            - The objectstore of the OSD, either filestore or bluestore
        required: true
        choices: ['bluestore', 'filestore']
    data:
        description:
            - The logical volume name or device to use for the OSD data.
        required: true
    data_vg:
        description:
            - If data is a lv, this must be the name of the volume group it belongs to.
        required: false
    journal:
        description:
            - The logical volume name or partition to use as a filestore journal.
            - Only applicable if objectstore is 'filestore'.
        required: false
    journal_vg:
        description:
            - If journal is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'filestore'.
        required: false
    db:
        description:
            - A partition or logical volume name to use for block.db.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    db_vg:
        description:
            - If db is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal:
        description:
            - A partition or logical volume name to use for block.wal.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal_vg:
        description:
            - If wal is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    crush_device_class:
        description:
            - Will set the crush device class for the OSD.
        required: false
    dmcrypt:
        description:
            - If set to True the OSD will be encrypted with dmcrypt.
        required: false
        type: bool
        default: false


author:
    - Andrew Schoen (@andrewschoen)
'''

EXAMPLES = '''
- name: set up a filestore osd with an lv data and a journal partition
  ceph_volume:
    objectstore: filestore
    data: data-lv
    data_vg: data-vg
    journal: /dev/sdc1

- name: set up a bluestore osd with a raw device for data
  ceph_volume:
    objectstore: bluestore
    data: /dev/sdc

- name: set up a bluestore osd with an lv for data and partitions for block.wal and block.db
  ceph_volume:
    objectstore: bluestore
    data: data-lv
    data_vg: data-vg
    db: /dev/sdc1
    wal: /dev/sdc2
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule
import datetime


def get_data(data, data_vg):
    if data_vg:
        data = "{0}/{1}".format(data_vg, data)
    return data


def get_journal(journal, journal_vg):
    if journal_vg:
        journal = "{0}/{1}".format(journal_vg, journal)
    return journal


def get_db(db, db_vg):
    if db_vg:
        db = "{0}/{1}".format(db_vg, db)
    return db


def get_wal(wal, wal_vg):
    if wal_vg:
        wal = "{0}/{1}".format(wal_vg, wal)
    return wal


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        subcommand=dict(type='str', required=False, default='lvm', choices=['lvm']),
        objectstore=dict(type='str', required=True, choices=['bluestore', 'filestore']),
        data=dict(type='str', required=True),
        data_vg=dict(type='str', required=False),
        journal=dict(type='str', required=False),
        journal_vg=dict(type='str', required=False),
        db=dict(type='str', required=False),
        db_vg=dict(type='str', required=False),
        wal=dict(type='str', required=False),
        wal_vg=dict(type='str', required=False),
        crush_device_class=dict(type='str', required=False),
        dmcrypt=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    cluster = module.params['cluster']
    subcommand = module.params['subcommand']
    objectstore = module.params['objectstore']
    data = module.params['data']
    data_vg = module.params.get('data_vg', None)
    journal = module.params.get('journal', None)
    journal_vg = module.params.get('journal_vg', None)
    db = module.params.get('db', None)
    db_vg = module.params.get('db_vg', None)
    wal = module.params.get('wal', None)
    wal_vg = module.params.get('wal_vg', None)
    crush_device_class = module.params.get('crush_device_class', None)
    dmcrypt = module.params['dmcrypt']

    cmd = [
        'ceph-volume',
        '--cluster',
        cluster,
        subcommand,
        'create',
        '--%s' % objectstore,
        '--data',
    ]

    data = get_data(data, data_vg)
    cmd.append(data)

    if journal:
        journal = get_journal(journal, journal_vg)
        cmd.extend(["--journal", journal])

    if db:
        db = get_db(db, db_vg)
        cmd.extend(["--block.db", db])

    if wal:
        wal = get_wal(wal, wal_vg)
        cmd.extend(["--block.wal", wal])

    if crush_device_class:
        cmd.extend(["--crush-device-class", crush_device_class])

    if dmcrypt:
        cmd.append("--dmcrypt")

    result = dict(
        changed=False,
        cmd=cmd,
        stdout='',
        stderr='',
        rc='',
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        return result

    # check to see if osd already exists
    # FIXME: this does not work when data is a raw device
    rc, out, err = module.run_command(["ceph-volume", "lvm", "list", data], encoding=None)
    if rc == 0:
        result["stdout"] = "skipped, since {0} is already used for an osd".format(data)
        result['rc'] = 0
        module.exit_json(**result)

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(cmd, encoding=None)

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

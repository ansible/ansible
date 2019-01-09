#!/usr/bin/python

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
author: "Bob ter Hark"
module: aix_mount
short_description: Mounts a filesystem on AIX
description:
  - This module mounts an existing filesystem
  - Or mount a AIX logical volume on a mountpoint
version_added: "2.2"
options:
  filesystem:
    description:
    - filesystem entry in /etc/filesystems or
    - mountpoint for the nfs mount
    - fs can used as alias
    aliases: fs
    required: true
  state:
    description:
    - Whether filesystem should be mounted or umounted
    default: present
    required: false
  nfsserver:
    description:
    - NFS server (requires also requires nfsexport)
    required: false
  nfsexport:
    description:
    - NFS export (required if nfsserver is present)
    required: false
notes:
  - tested on AIX
'''

EXAMPLES = '''
# Mount the existing (present in /etc/filesystems) /data filesystem
- aix_mount: fs=/data

# Unmount the filesystem mounted on /mnt
- aix_mount: fs=/mnt state=absent

# Mount a NFS share
- aix_mount:
    fs: /mnt
    nfsserver: nimserver.local
    nfsexport: /export/nim/tmp

more examples will follow
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filesystem=dict(required=True, aliases=['fs']),
            state=dict(choices=['absent', 'present'], default='present'),
            nfsserver=dict(),
            nfsexport=dict(),
        ),
        supports_check_mode=True,
    )

    fs = module.params['filesystem']
    state = module.params['state']
    nfsserver = module.params['nfsserver']
    nfsexport = module.params['nfsexport']

    changed = False

    # check if filesystem is mounted
    # using df to check if the filesystem is mounted
    cmd = module.get_bin_path('df', required=True)
    rc, out, err = module.run_command("%s %s" % (cmd, fs))
    if rc != 0:
        # filesystem is not mounted and directory does not exist
        df_mounted_filesystem = ''
    else:
        # filesystem is either mounted or mountpoint is present
        # retrieve last word from out. This will be the filesystem
        # if it is mounted
        output_list = out.rstrip().split()
        df_mounted_filesystem = output_list[-1]

    if df_mounted_filesystem == fs:
        # Filesystem is mounted
        if state == 'present':
            # nothing to do
            module.exit_json(changed=False)
        else:
            if module.check_mode:
                # filesystem should be absent
                # but in check mode, just exit
                module.exit_json(changed=True)

    else:
        # Filesystem is not mounted
        if state == 'absent':
            # nothing to do
            module.exit_json(changed=False)
        else:
            if module.check_mode:
                # filesystem should be present
                # but in check mode, just exit
                module.exit_json(changed=True)

    # the work starts here
    if df_mounted_filesystem == fs:
        # Filesystem is mounted and must be unmounted
        cmd = module.get_bin_path('umount', required=True)
        rc, out, err = module.run_command("%s %s" % (cmd, fs))
        if rc == 0:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="Error: umount filesystem %s failed." % (fs),
                             rc=rc, err=err)

    else:
        # Filesystem is not mounted and must be mounted

        # check if filesystem exists
        # lsfs returns 0 if the filesystem is present in /etc/filesystem
        # or 1 (lsfs: 0506-915 No record matching ... was found in
        # /etc/filesystems.)
        cmd = module.get_bin_path('lsfs', required=True)
        rc, out, err = module.run_command("%s %s" % (cmd, fs))
        if rc == 0:
            # filesystem exists in /etc/filesystem
            # mount the filesystem with 'mount <filesystem>'
            cmd = module.get_bin_path('mount', required=True)
            rc, out, err = module.run_command("%s %s" % (cmd, fs))
            if rc == 0:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg="Error: mount filesystem %s failed."
                                 % (fs), rc=rc, err=err)

        else:
            # filesystem does not exists and must be mounted
            # only nfs possible at this moment

            if not (nfsexport and nfsserver):
                module.fail_json(msg=("Error: filesystem not present in"
                                 " in /etc/filesystems or nfsserver and"
                                 " nfsexport options missing"))

            # check for existence of directory
            if not os.path.isdir(fs):
                module.fail_json(msg="Error: directory %s does not exist."
                                 % (fs))

            if module.check_mode:
                module.exit_json(changed=True)

            # create the mount command
            cmd = module.get_bin_path('mount', required=True)
            rc, out, err = module.run_command("%s %s:%s %s" % (cmd, nfsserver,
                                              nfsexport, fs))
            if rc != 0:
                module.fail_json(msg="Error: mount filesystem %s failed."
                                 % (fs), rc=rc, err=err)
            module.exit_json(changed=True)

if __name__ == '__main__':
    main()

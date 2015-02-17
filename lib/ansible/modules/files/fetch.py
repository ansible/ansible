# this is a virtual module that is entirely implemented server side

DOCUMENTATION = '''
---
module: fetch
short_description: Fetches a file from remote nodes
description:
     - This module works like M(copy), but in reverse. It is used for fetching
       files from remote machines and storing them locally in a file tree,
       organized by hostname. Note that this module is written to transfer
       log files that might not be present, so a missing remote file won't
       be an error unless fail_on_missing is set to 'yes'.
version_added: "0.2"
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a
        directory. Recursive fetching may be supported in a later release.
    required: true
    default: null
    aliases: []
  dest:
    description:
      - A directory to save the file into. For example, if the I(dest)
        directory is C(/backup) a I(src) file named C(/etc/profile) on host
        C(host.example.com), would be saved into
        C(/backup/host.example.com/etc/profile)
    required: true
    default: null
  fail_on_missing:
    version_added: "1.1"
    description:
      - Makes it fails when the source file is missing.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  validate_checksum:
    version_added: "1.4"
    description:
      - Verify that the source and destination checksums match after the files are fetched.
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
    aliases: [ "validate_md5" ]
  flat:
    version_added: "1.2"
    description:
      - Allows you to override the default behavior of prepending
        hostname/path/to/file to the destination.  If dest ends with '/', it
        will use the basename of the source file, similar to the copy module.
        Obviously this is only handy if the filenames are unique.
requirements: []
author: Michael DeHaan
'''

EXAMPLES = '''
# Store file into /tmp/fetched/host.example.com/tmp/somefile
- fetch: src=/tmp/somefile dest=/tmp/fetched

# Specifying a path directly
- fetch: src=/tmp/somefile dest=/tmp/prefix-{{ ansible_hostname }} flat=yes

# Specifying a destination path
- fetch: src=/tmp/uniquefile dest=/tmp/special/ flat=yes

# Storing in a path relative to the playbook
- fetch: src=/tmp/uniquefile dest=special/prefix-{{ ansible_hostname }} flat=yes
'''

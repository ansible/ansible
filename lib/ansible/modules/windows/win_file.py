#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_file
version_added: "1.9.2"
short_description: Creates, touches or removes files, directories, and links
description:
- Sets attributes of files, symlinks, junction points, hard links, and
  directories.
- Can be used to create and remove files, links, and directories.
- Unlike M(file), does not modify the permissions of the object, use M(win_acl)
  instead.
- For non-Windows targets, use the M(file) module instead.
notes:
- See also M(win_copy), M(win_template), M(win_acl), M(copy), M(template),
  M(assemble).
author:
- Jon Hawkesworth (@jhawkesworth)
- Jordan Borean (@jborean93)
options:
  access_time:
    description:
    - Set's the last access time attribute on the file.
    - If not set, will default to C(now) when C(state=touch) and C(preserve)
      for other states.
    - If C(now), will set to the current datetime and is not idempotent.
    - If C(preserve), will keep the existing value.
    - Otherwise this is set to the datetime in the format specified by
      I(access_time_format).
    version_added: '2.7'
  access_time_format:
    description:
    - The datetime format of the I(access_time) value.
    - This is based on the .NET Framework custom datetime string format values.
    - See U(https://docs.microsoft.com/en-us/dotnet/standard/base-types/custom-date-and-time-format-strings)
      for optional values.
    default: 'yyyyMMddHHmm.ss'
    version_added: '2.7'
  attributes:
    description:
    - Attributes the file or directory that should be set.
    - Some attributes are mutually exclusive from each other.
    - To remove an attribute, prefix the value with C(-).
    - C(encrypted) requires the user's credentials to be available on the
      process, this can commonly be done by setting C(become=yes) on the task.
    - Description of each attribute and what they mean can be found here
      U(https://msdn.microsoft.com/en-us/library/system.io.fileattributes.aspx).
    choices:
    - archive
    - compressed
    - encrypted
    - hidden
    - normal
    - no_scrub_data
    - not_content_indexed
    - offline
    - read_only
    - sparse_file
    - system
    - temporary
    type: list
    version_added: '2.7'
  creation_time:
    description:
    - Set's the creation time attributes on the file.
    - If C(now), will set to the current datetime and is not idempotent.
    - If C(preserve), will keep the existing value.
    - Otherwise this is set to the datetime in the format specified by
      I(creation_time_format).
    version_added: '2.7'
    default: preserve
  creation_time_format:
    description:
    - The datetime format of the I(creation_time) value.
    - This is based on the .NET Framework custom datetime string format values.
    - See U(https://docs.microsoft.com/en-us/dotnet/standard/base-types/custom-date-and-time-format-strings)
      for optional values.
    default: 'yyyyMMddHHmm.ss'
    version_added: '2.7'
  follow:
    description:
    - When set, will follow I(path) if it points to a symbolic link or a
      junction point.
    - If I(state) is C(hard), C(junction), or C(link), it will follow I(src)
      and not I(path) when creating the link and will then follow I(path) when
      setting the attributes, timestamps and permissions.
    - If I(state) is C(absent), then this value is ignored.
    - Will recursively follow links until the target is a normal file or
      directory.
    type: bool
    default: 'yes'
    version_added: '2.7'
  force:
    description:
    - Force the creation of symbolic links or junction points in two cases;
      I(src) does not exist or I(path) is already a directory or file.
    - Will not change a directory to a link or junction if it is not empty.
    type: bool
    default: 'no'
    version_added: '2.7'
  group:
    description:
    - The user or group of the primary group.
    - This field is kept for backwards compatibility or interop with POSIX
      systems.
    - Can be the name or SID of an account.
    version_added: '2.7'
  path:
    description:
    - The path to the file being managed.
    required: yes
    type: path
    aliases:
    - dest
    - name
  owner:
    description:
    - User user or group assigned as the owner of the file.
    - Can be the name or SID of an account.
    - Require the C(SeRestorePrivilege) if setting an owner that is not the
      current user.
    version_added: '2.7'
  src:
    description:
    - The path of the file or directory to link to.
    - This only applies to C(state=hard), C(state=junction), or C(state=link).
    - Can be absolute, relative or nonexisting path, relative paths are relative
      to the path set by I(path).
    - If C(state=hard), MUST be on the same volume as I(path) and relative paths
      will be resolved to the absolute path.
    - If C(state=junction), MUST be on the same volume as I(path) and relative
      paths will be resolved to the absolute path.
    - If C(state=link), can be a relative or absolute path to a file or
      directory on the same or a different volume.
    - C(state=junction), and C(state=link) allow non-existing paths when
      I(force) is C(True), when C(state=hard), I(src) MUST exist.
    type: path
    version_added: '2.7'
  state:
    description:
    - If C(absent), directories will be recursively deleted, files or links
      will be removed.
    - If C(directory), all intermediate subdirectories will be created if they
      do not exist.
    - If C(file), the fille will NOT be created if it does not exist, use
      C(touch) or M(win_copy)/M(win_template) if you want that behaviour.
    - If C(hard), will create a hard link that is linked to the file at I(src),
      this hard link target must exist.
    - If C(junction), will create a junction point that is linked to the
      directory at I(src), the target must exist on the same volume and be the
      absolute path to the directory.
    - If C(link), will create a symbolic link that is linked to the first or
      directory at I(src), the target can be an absolute or relative path to
      a file or directory.
    - If C(touch), an empty file will be created if C(path) does not exist,
      while an existing file or directory will have its last access and write
      times set to the current systemt ime (similar to the way C(touch) works
      from the command line).
    - The default is C(file) if I(path) does not exist, otherwise it is the
      type of file at I(path).
    - C(hard), C(junction), and C(link) were added in Ansible 2.7.
    choices:
    - absent
    - directory
    - file
    - hard
    - junction
    - link
    - touch
  write_time:
    description:
    - Set's the last write time attribute on the file.
    - If not set, will default to C(now) when C(state=touch) and C(preserve)
      for other states.
    - If C(now), will set to the current datetime and is not idempotent.
    - If C(preserve), will keep the existing value.
    - Otherwise this is set to the datetime in the format specified by
      I(write_time_format).
    version_added: '2.7'
  write_time_format:
    description:
    - The datetime format of the I(write_time) value.
    - This is based on the .NET Framework custom datetime string format values.
    - See U(https://docs.microsoft.com/en-us/dotnet/standard/base-types/custom-date-and-time-format-strings)
      for optional values.
    default: 'yyyyMMddHHmm.ss'
    version_added: '2.7'
'''

EXAMPLES = r'''
- name: Touch a file (creates if not present, updates write and access time if present)
  win_file:
    path: C:\Temp\foo.conf
    state: touch

- name: Ensure a file exists without modifying access and write time
  win_file:
    path: C:\Users\ansible\Documents\ansible.log
    state: touch
    access_time: preserve
    write_time: preserve

- name: Remove a file, if present
  win_file:
    path: C:\Temp\foo.conf
    state: absent

- name: Create directory structure
  win_file:
    path: C:\Temp\folder\subfolder
    state: directory

- name: Remove directory structure
  win_file:
    path: C:\Temp
    state: absent

- name: create a directory that is hidden and owned by Administrators
  win_file:
    path: C:\Temp\directory
    state: directory
    owner: Administrators
    attributes:
    - hidden

- name: ensure a directory is not hidden with the datestamp 6:30:05 am on the 1st of January 2018
  win_file:
    path: C:\Temp\directory
    state: directory
    attributes:
    - -hidden
    access_time: 201801010630.05
    creation_time: 201801010630.05
    write_time: 201801010630.05

- name: touch a file ensuring it is hidden, an archive, read only but not a system file
  win_file:
    path: C:\ansible\output.txt
    state: touch
    attributes:
    - hidden
    - archive
    - read_only
    - -system

- name: create a symbolic link
  win_file:
    path: C:\my_documents
    src: C:\Users\ansible\Documents
    state: link
'''

RETURN = r'''
path:
  description: the absolute path of the file that was managed
  returned: always
  type: string
  sample: C:\Windows
'''

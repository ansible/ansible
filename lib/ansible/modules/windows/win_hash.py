#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Harry Saryan  <hs-hub-world@github>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_hash
version_added: "2.10"
short_description: generate a hash file and detect changes in a folder.
description:
     - Generate a hash file by parsing folder content.
     - Detect file hash changes in the folder.
     - Exclude or Include specific files.
     - Can be used to detect and trigger repair/reinstall of packaged items (i.e. choco)
options:
  path:
    description:
      - path to parse files and generate a hash against it.
    type: str
    required: yes
  hashfilepath:
    description:
      - optional - where do you want the hash file to be saved. By default it will saved in the same path as the 'path' option.
    type: str
    required: no
  hashfilename:
    description:
      - optional - the file name you generate and store hash strings
      - default hash file name is '.ans_hash'
    type: str
    required: no
  FilestoExclude:
    description:
      - optional - list of files to exclude from generating and detecting hash changes
      - this is usefull when you know some files content will be changes and you don't care to detect the changes
    type: list
    required: no
  FilesToInclude:
    description:
      - optional - list of file names to include for generating and detecting hash changes.
      - note this takes precendece over FilestoExclude.
    type: list
    required: no
  reset:
    description:
      - optional - regenerate the hash file.
      - this is usefull when you know a module is going to make a change to the folder content you would want to regenerate the hash.
    type: bool
    required: no
seealso:
- module: win_stat
- module: win_chocolatey
author:
  - Harry Saryan (@hs-hub-world)
'''

EXAMPLES = r'''
- name: 'Generate/Detect folder hash changes c:\\My_App'
  win_hash:
    path: 'c:\\My_App'
  register: MyApp

- name: 'ReInstall MyApp Choco Package when Hash Changes are detected'
  win_chocolatey:
    name: My_App
    state: 'reinstalled'
  when: MyApp.changed == True
  register: choco_myapp

- name: 'Generate folder hash after choco re-install My_App'
  win_hash:
    path: 'c:\\My_App'
    reset: true
  when: choco_myapp.changed == true

- name: 'Generate folder hash with exclusion list c:\\My_App'
  win_hash:
    path: 'c:\\My_App'
    FilestoExclude:
      - 'web.config'
      - 'packages.config'
'''

RETURN = r'''
hashfileexists:
  description:
    - Shows if the previously generated hash file already exists.
    - if not exist that means new one will be generated.
  returned: always
  type: bool
  sample: "True"
FilestoExclude:
  returned: always
  description:
    - Shows list of excluded files defined in the yml file
  type: list
  sample: '[web.config, packages.config]'
path:
  returned: always
  description:
    - Shows the main src path where all file hashes are compared.
  type: str
  sample: 'c:\\My_App'
hashmatches:
  returned: always
  description:
    - returns True if all HASHES matches. Similar to (changed=false)
  type: bool
  sample: "True"
FilesToInclude:
  returned: always
  description:
    - Shows list of included files being monitored defined in the yml file.
    - Note FilesToInclude takes precedence over FilestoExclude.
  type: list
  sample: "[myapp.dll]"
NewHashGenerated:
  returned: always
  description:
    - Will return true if a new Hash file was generated.
    - If a new hash file is generated that means no change will be detect until next run
    - 'Value=True (initial run, establish baseline)'
    - 'Value=False (subsequent runs, compare files against baseline.)'
  type: bool
  sample: "True"
ChangedFiles:
  returned: always
  description:
    - Will return list of changed files.
    - 'Includes deleted, renamed, content modified Files.'
  type: list
  sample: '[log4net.dll, web.config]'
hashfilepath:
  returned: always
  description:
    - Returns full path to the Hash File.
    - This file is generated during first run or when reset=true option is used.
    - This file holds the list of  hashes which are compares against current files in the dir.
  type: str
  sample: 'c:\\My_App\.ans_hash'
changed:
  returned: always
  description:
    - Returns true if any change is detected
    - Returns false if no changes are detected
    - You may use this to trigger other modules (i.e. choco reinstall myapp)
  type: bool
  sample: "False"
HashGenTime:
  description:
    - Returns the date time when the hash file was generated
    - You may use this to get a sense when the hash baseline was generated.
  returned: always
  type: str
  sample: "01/06/2020 08:23:39.908"
message:
  returned: always
  description:
    - Returns execution steps for easier troubleshooting.
  type: str
  sample: 'Doing Reset. Hash not found, generating new hash file'
pathmissing:
  returned: always
  description:
    - Returns True if the provided 'Path' value is missing (i.e. c:\\MyApp)
  type: bool
  sample: "False"
'''

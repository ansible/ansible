#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module:  vmware_guest_move 

short_description:  move a named vm to a named destination folder in a named datacenter

version_added: "2.4"

description:
    - "move a vm to a specific vm folder in a specific datacenter"


extends_documentation_fragment:
    - vmware_guest

author:
    - Saar Grin (@saargrin)
'''

EXAMPLES = '''
# move vm
- hosts: localhost
  tasks:
    - name: move vm to folder
      vmware_move_guest:
       name: "xxxxx"
       dst_folder: "TopFolder/Subfolder"
       datacenter: "DC"
       hostname : "vc1.corp.sample.com"
       username : "username"
       password :  "password"
       validate_certs: false

      register: result

    - debug: var=result
'''

RETURN = '''
message:
    description: details of procedure
'''




from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    connect_to_api,
    gather_vm_facts,
    get_all_objs,
    compile_folder_path_for_object,
    vmware_argument_spec,
    find_datacenter_by_name
)
from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect, SmartConnect, GetSi

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False




def connectVC(vcenter,user,password):
 try:
  print "Trying to connect to VCENTER SERVER . . ."
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
  context.verify_mode = ssl.CERT_NONE
  si = connect.Connect(vcenter,443,user,password,sslContext=context)
 except IOError, e:
  pass
  atexit.register(Disconnect, si)
 print "Connected to VCENTER SERVER !"
 return (si)

def getVM(si,name):
 root_folder = si.content.rootFolder
 for datacenter in root_folder.childEntity:
  search_index = si.content.searchIndex
  vm = search_index.FindByDnsName(datacenter, name,vmSearch=True)
  print vm,vm.name
 return (vm)

def getFolder(si,path):
 root_folder = si.content.rootFolder
 for datacenter in root_folder.childEntity:
  search_index = si.content.searchIndex
  folder = search_index.FindByInventoryPath(path)
  print folder
 return (folder)

def main():
    mod = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            dst_folder=dict(required=True),
            hostname= dict(required=True),
            datacenter=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            validate_certs=dict(required=True)
        )
    )

    name = mod.params["name"]
    dst =  mod.params["dst_folder"]
    hostname = mod.params["hostname"]
    datacenter=mod.params["datacenter"]
    path = str(datacenter+"/vm/"+dst)
    username=mod.params["username"]
    password=mod.params["password"]
    si = connectVC(hostname,username,password)
    vm = getVM(si,name)
    folder = getFolder (si,path)
    move_task = folder.MoveInto([vm])
    status = str("move vm:"+name+" id: "+str(vm)+" to folder: "+str(folder.name) )
    mod.exit_json(msg=status,changed=True)





if __name__ == '__main__':
    main()


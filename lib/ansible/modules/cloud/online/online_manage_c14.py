#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: online_manage_c14
short_description: Manage C14 storage.
description:
  - Manage all features of C14 storage solution.
  - U(https://www.online.net/fr/c14)
  - The Online API with C14 methods : U(https://console.online.net/fr/api)
  - The module needs pysftp to be installed on the managed node (pip install pysftp)
version_added: "2.8"
author:
  - "Broferek (@broferek)"
extends_documentation_fragment: online
'''

EXAMPLES = r'''
- name: Get all archives
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "get_archives"

- name: Get a specific archive
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "get_archives"
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    
- name: Get all safes
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "get_safes"

- name: Create a C14 archive
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "create_archive"
    archive_details:
      safe_uuid: "qsdfaereqd554-qsdfqs24qsd"
      name: "Test archive"
      description: "Description for test archive"
      parity: optional (default="standard")
      crypto: optional (default="aes-256-bc")
      days: optional (default=7)
      protocols: optional (default=["SSH"])
      ssh_keys: optional (default=[])
      platforms: optional (default=["2"])

- name: Upload some files or directories
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "upload_files"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    paths: 
      - "/tmp/foo.txt"
      - "/tmp/bar"

- name: Download some files or directories
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "download_files"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    paths: 
      - "foo.txt"
      - "bar"
    download_path: "/tmp"
          
- name: Get a list of files or directories stored in the archive
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "get_files"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"

- name: Remove some files or directories in the archive
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "remove_files"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    paths: 
      - "foo.txt"
      - "bar"
                         
- name: Freeze an archive and wait for it to be freezed
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "freeze_archive"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    wait: true

- name: Freeze an archive and do not wait for it to be freezed
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "freeze_archive"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"

- name: Unfreeze an archive and wait for it to be freezed
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "unfreeze_archive"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    wait: true

- name: Unfreeze an archive and do not wait for it to be freezed
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "unfreeze_archive"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
 
- name: Delete an archive key (can only be performed if the archive is freezed)
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "delete_archive_key"
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"

- name: Set an archive key
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "set_archive_key"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
    archive_key: "{{ 'This is a test string' | hash('sha1') }}"          

- name: Get an archive key
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "get_archive_key"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"

- name: Remove an archive
  online_manage_c14:
    api_token: "qsfda9964-foo-sghz8751-bar"
    operation: "remove_archive"    
    archive_uuid: "qsdfqsdfd5454-sdfqsdgaergv8755"
      
'''

RETURN = r'''
---
online_manage_c14:
  description: The result of your operation
  returned: success
  type: complex
  contains:
    "result": "Description of the result of your operation
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.online import (
    Online, OnlineException, online_argument_spec
)
import pysftp
import math
import os
import time
import shutil
import posixpath
from stat import S_ISDIR

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

class OnlineManageC14(Online):

    def __init__(self, module):
        super(OnlineManageC14, self).__init__(module)
        
    def find_safe_uuid_from_archive(self,archive_uuid):
        archives = self.get_archives()
        for archive in archives:
            if archive['uuid'] == archive_uuid:
                return archive['uuid_safe']
        self.module.fail_json(msg='The archive {0} does not exist'.format(archive_uuid))

    def find_archive_location_id(self,safe,archive_uuid): 
        self.name = 'storage/c14/safe/{0}/archive/{1}/location'.format(safe,archive_uuid)
        location = self.get_resources()
        return location[0]['uuid_ref']
    
    def get_safes(self):
        self.name = 'storage/c14/safe'        
        return self.get_resources()
        

    def get_archives(self,archive_uuid=None):
        self.name = 'storage/c14/archive'
        archives = self.get_resources()
        result = list()        
        for archive in archives:
            if archive_uuid == archive['uuid_ref'] or archive_uuid is None:                
                result.append(
                    {
                        'name': archive['name'],
                        'status': archive['status'],
                        'uuid': archive['uuid_ref'],
                        'parity': archive['parity'],
                        'creation_date': archive['creation_date'],
                        'description': archive['description'],
                        'uuid_safe': archive['safe']['uuid_ref'],                        
                        'size': convert_size(int(archive['size'])) if archive.has_key('size') else 'Unavailable'                        
                    }
                )                                     
        return result

    def get_bucket(self,archive_uuid):
        bucket = None
        if archive_uuid is None:
            self.module.fail_json(msg='Missing mandatory parameter: archive_uuid')
        safe = self.find_safe_uuid_from_archive(archive_uuid)
        self.name = 'storage/c14/safe/{0}/archive/{1}/bucket'.format(safe,archive_uuid)
        result = self.get('/%s' % self.name)
        
        if result.ok:
            bucket = result.json['credentials'][0]
        return bucket
        
    def get_files(self,archive_uuid):
        if archive_uuid is None:
            self.module.fail_json(msg='Missing mandatory parameter: archive_uuid')        
        with pysftp.Connection(**self.get_credentials(archive_uuid)) as sftp:
            sftp_files = list()
            sftp_directories = list()
            sftp_root_directories = set()
            sftp.walktree('.', fcallback=sftp_files.append, dcallback=sftp_directories.append, ucallback=self.sftp_do_nothing)
            for directory in sftp_directories:            
                sftp_root_directories.add(directory.split('/')[1])                
            self.module.exit_json(files=sftp_files, directories=sftp_directories, root_directories=sftp_root_directories)

    def rmtree(self, sftp, remotepath, level=0):
        for f in sftp.listdir_attr(remotepath):
            rpath = posixpath.join(remotepath, f.filename)
            if S_ISDIR(f.st_mode):
                self.rmtree(sftp, rpath, level=(level + 1))
            else:
                rpath = posixpath.join(remotepath, f.filename)
                sftp.remove(rpath)
        sftp.rmdir(remotepath)   

    def remove_files(self, archive_uuid, paths):   
        with pysftp.Connection(**self.get_credentials(archive_uuid)) as sftp:
            for path in paths:
                if sftp.exists(path):
                    self.rmtree(sftp,path)
            self.module.exit_json(changed='true', result='Files have been removed')

    def sftp_do_nothing(self):
        pass
    
    def get_credentials(self,archive_uuid):
        bucket = self.get_bucket(archive_uuid)
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None        
        sftp_creds = {
            'host': bucket['uri'].split('@')[1].split(':')[0],
            'port': int(bucket['uri'].split('@')[1].split(':')[1]),
            'username': bucket['login'],
            'password': bucket['password'],
            'cnopts': cnopts
        }   
        return sftp_creds
    
    def upload_files(self, paths, archive_uuid):
        try:
            with pysftp.Connection(**self.get_credentials(archive_uuid)) as sftp:
                for path in paths:
                    if os.path.isfile(path):
                        sftp.put(path)
                    elif os.path.isdir(path):
                        directory = path.split('/')[-1]
                        if not sftp.exists(directory):
                            sftp.mkdir(directory)                     
                        sftp.put_r(path,directory)
                    else:
                        self.module.fail_json(msg='No such file or directory : ' + path)
            self.module.exit_json(msg='All files or directories have been uploaded in ' + archive_uuid)
        except OnlineException as exc:
            self.module.fail_json(msg=exc.message)
    
    def download_files(self, paths, download_path, archive_uuid):
        try:
            with pysftp.Connection(**self.get_credentials(archive_uuid)) as sftp:
                for path in paths:
                    download_path = download_path + '/'
                    if sftp.exists(path):  
                        if sftp.isdir(path):
                            if os.path.exists(download_path + path):
                                shutil.rmtree(download_path + path)
                            if not os.path.exists(download_path):    
                                os.mkdir(download_path)
                            sftp.get_r(path, download_path)
                        elif sftp.isfile(path):
                            sftp.get(path, download_path + path) 
                    else:
                        self.module.fail_json(msg='No such file or directory : ' + path)                    
            self.module.exit_json(msg='All files or directories have been downloaded')
        except OnlineException as exc:
            self.module.fail_json(msg=exc.message)
        
    def create_archive(self, archive_details):
        if archive_details is None:
            self.module.fail_json(msg='Missing mandatory parameter: archive_details')
        if not archive_details.has_key('safe_uuid'):
            self.module.fail_json(msg='Missing mandatory parameter: archive_details["safe_uuid"]')
        elif not archive_details.has_key('name'):
            self.module.fail_json(msg='Missing mandatory parameter: archive_details["name"]')
        elif not archive_details.has_key('description'):
            self.module.fail_json(msg='Missing mandatory parameter: archive_details["description"]')

        self.name = 'storage/c14/safe/{0}/archive'.format(archive_details['safe_uuid'])
            
        post_data = dict(
            safe_id=archive_details['safe_uuid'],
            name=archive_details['name'],
            description=archive_details['description'],
            parity=archive_details['parity'] if archive_details.has_key('parity') is None else 'standard',
            crypto=archive_details['crypto'] if archive_details.has_key('crypto') is None else 'aes-256-cbc',
            days=archive_details['days'] if archive_details.has_key('days') is None else 7,
            protocols=archive_details['protocols'] if archive_details.has_key('protocols') is None else ['SSH'],
            ssh_keys=archive_details['ssh_keys'] if archive_details.has_key('ssh_keys') is None else [],
            platforms=archive_details['platforms'] if archive_details.has_key('platforms') is None else ["2"]
        )

        result = self.post('/%s' % self.name, post_data)
        self.module.exit_json(result=result.json)
    
    def freeze_archive(self, archive_uuid, wait):
        safe = self.find_safe_uuid_from_archive(archive_uuid)        
        self.name = 'storage/c14/safe/{0}/archive/{1}/archive'.format(safe, archive_uuid)
        post_data = dict()
        result = self.post('/%s' % self.name, post_data)
        time.sleep(5)
        if wait:
            while True:
                archive = self.get_archives(archive_uuid)
                if archive[0]['status'] == 'active':
                    break
                else:
                    time.sleep(30)
        self.module.exit_json(result=result.json)

    def unfreeze_archive(self, archive_uuid, archive_key, wait):
        if archive_key is None:
            self.module.fail_json(msg='Missing mandatory parameter: archive_key')        
        safe = self.find_safe_uuid_from_archive(archive_uuid)
        location_id = self.find_archive_location_id(safe,archive_uuid)
        
        self.name = 'storage/c14/safe/{0}/archive/{1}/unarchive'.format(safe, archive_uuid)
        
        post_data = dict(
            protocols = ['SSH'],
            location_id = location_id,
            key = archive_key
        )
        result = self.post('/%s' % self.name, post_data)
        time.sleep(5)
        if wait:
            while True:
                archive = self.get_archives(archive_uuid)
                if archive[0]['status'] == 'active':
                    break
                else:
                    time.sleep(30)
        self.module.exit_json(result="The archive {0} has been unfreezed".format(archive_uuid))

    def remove_archive(self, archive_uuid):
        safe = self.find_safe_uuid_from_archive(archive_uuid)        
        
        bucket = self.get_bucket(archive_uuid)
        if bucket is not None:
            self.module.fail_json(msg='An open temporary space can not be removed. Freeze the archive {0} first'.format(archive_uuid))
            
        self.name = "storage/c14/safe/{0}/archive/{1}".format(safe,archive_uuid)
        delete_data = dict()
        result = self.delete('/%s' % self.name, delete_data)
        
        self.module.exit_json(result='The archive {0} is scheduled to be removed'.format(archive_uuid))

    def get_archive_key(self, archive_uuid):
        safe = self.find_safe_uuid_from_archive(archive_uuid)
        self.name = "storage/c14/safe/{0}/archive/{1}/key".format(safe,archive_uuid)
        key = self.get('/%s' % self.name)
        self.module.exit_json(result=key.json)
        
    def set_archive_key(self, archive_uuid, archive_key):
        safe = self.find_safe_uuid_from_archive(archive_uuid)
        self.name = "storage/c14/safe/{0}/archive/{1}/key".format(safe,archive_uuid)
        post_data = dict(
            key = archive_key
        )
        result = self.post('/%s' % self.name, post_data)
        if result.json is None:
            self.module.exit_json(result="The archive key has been set")
        else:        
            self.module.exit_json(result=result.json)        

    def delete_archive_key(self, archive_uuid, archive_key):
        safe = self.find_safe_uuid_from_archive(archive_uuid)
        self.name = "storage/c14/safe/{0}/archive/{1}/key".format(safe,archive_uuid)
        delete_data = dict()
        result = self.delete('/%s' % self.name, delete_data)
        if result.json is None:
            self.module.exit_json(result="The archive key has been deleted")
        else:
            self.module.exit_json(result=result.json)          
        
def main():
    argument_spec = online_argument_spec()
    argument_spec.update(
        dict(
            operation=dict(
                required=True,
                choices=['get_archives','get_safes','get_bucket','get_files','get_archive_key','set_archive_key','delete_archive_key','create_archive','upload_files','download_files','freeze_archive','unfreeze_archive','remove_archive','remove_files']
            ),
            archive_uuid=dict(),
            archive_key=dict(),
            archive_details=dict(
                type = dict
            ),
            paths=dict(
                type = list,
                aliases=['path']
            ),
            download_path=dict(
                default='/tmp'
            ),
            wait=dict(
                default=False
            )
        )
    )
    
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    operation = module.params['operation']
    archive_uuid = module.params['archive_uuid']
    paths =  module.params['paths']
    download_path =  module.params['download_path']
    archive_details =  module.params['archive_details']    
    archive_key =  module.params['archive_key']
    wait = module.params['wait']
    
    try:
        if operation == 'get_archives':
            result = OnlineManageC14(module).get_archives(archive_uuid)
        elif operation == 'get_safes':
            result = OnlineManageC14(module).get_safes()
        elif operation == 'get_bucket':
            result = OnlineManageC14(module).get_bucket(archive_uuid)
        elif operation == 'get_files':
            result = OnlineManageC14(module).get_files(archive_uuid)
        elif operation == 'get_archive_key':
            result = OnlineManageC14(module).get_archive_key(archive_uuid)
        elif operation == 'set_archive_key':
            result = OnlineManageC14(module).set_archive_key(archive_uuid, archive_key)
        elif operation == 'delete_archive_key':
            result = OnlineManageC14(module).delete_archive_key(archive_uuid, archive_key)                                                                      
        elif operation == 'create_archive':
            result = OnlineManageC14(module).create_archive(archive_details)
        elif operation == 'upload_files':
            result = OnlineManageC14(module).upload_files(paths, archive_uuid)
        elif operation == 'download_files':
            result = OnlineManageC14(module).download_files(paths, download_path, archive_uuid)
        elif operation == 'freeze_archive':
            result = OnlineManageC14(module).freeze_archive(archive_uuid, wait)
        elif operation == 'unfreeze_archive':
            result = OnlineManageC14(module).unfreeze_archive(archive_uuid, archive_key, wait)
        elif operation == 'remove_archive':
            result = OnlineManageC14(module).remove_archive(archive_uuid)
        elif operation == 'remove_files':
            result = OnlineManageC14(module).remove_files(archive_uuid, paths)
                    
        module.exit_json(result=result)
    except OnlineException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()

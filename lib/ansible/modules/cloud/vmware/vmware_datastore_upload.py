#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Dag Wieers (@dagwieers) <dag@wieers.com>
# Copyright: (c) 2018, James E. King III (@jeking3) <jking@apache.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# TODO
# - make unit tests
# - test what happens when the first host is down, goes to second
# - test what happens if all hosts are down

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: vmware_datastore_upload
short_description: Upload a local file to a VMware datastore.
description:
    - Upload a local file to a VMware datastore with the option to
      skip the upload if the file already exists and is the same.
author:
    - "James E. King III (@jeking3) <jking@apache.org>"
version_added: 2.8
notes:
    - Tested on vSphere 6.7
requirements:
    - python >= 2.6
    - PyVmomi
options:
    datacenter:
      description:
        - Name of the datacenter containing the datastore.
        - If not specified, and more than one datastore with the
          same name exists, the action will fail.
      aliases: ['datacenter_name']
      required: no
      type: str
    datastore:
      description:
      - Name of datastore that will store the file.
      aliases: ['datastore_name']
      required: yes
      type: str
    source:
      description:
      - The full path of the local file to push to vCenter.
      required: yes
      type: str
    destination:
      description:
      - The full path to the destination file in the datastore.
      required: yes
      type: str
    debounce:
      description:
        - Uploading large files unnecessarily can be avoided
          with the C(debounce) option.
        - C(hash) will hash C(source) (using SHA256) and check
          for a file named C(<destination>.sha256) - if that file
          does not exist, or the hash in that file differs from
          the local hash, the file is uploaded and the hash is
          placed into C(<destination>.sha256) to debounce the next
          upload.  This option requires no write access locally.
        - C(hashcache) is the same as C(hash) except that it requires
          local write access to C(<source>.sha256) so the hash can
          be cached locally.  If C(source) is modified then the hash
          will be recalculated on the next upload.  This option
          prevents the local server from re-hashing large data files.
        - If C(none), the file will always be uploaded and no
          C(.sha256) files will be used.  This is appropriate
          for smaller files.
      default: none
      choices: [ none, hash, hashcache ]
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Upload, overwriting any existing file at the destination.
  vmware_datastore_upload:
    hostname: "10.0.1.1"
    username: "myuser"
    password: "mypass"
    datastore: "Dev"
    source: "/data/linux.iso"
    destination: "/ISO/linux.iso"
'''

RETURN = '''
results:
    description: result of the operation
    returned: always
    type: dict
    sample:
      "changed": true
      "msg": "File '/data/linux.iso' uploaded to '[Dev] ISO/linux.iso' through host 10.0.1.100."
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec

import ansible.module_utils.six.moves.urllib.parse as urllib_parse
import atexit
import hashlib
import mmap
import os


class VmwareDatastoreUploadMgr(PyVmomi):
    def __init__(self, module):
        ''' Prepares for the upload. '''
        super(VmwareDatastoreUploadMgr, self).__init__(module)
        datacenter_name = self.params.get('datacenter')
        datastore_name = self.params.get('datastore')
        self._datacenter = None
        if datacenter_name:
            self._datacenter = self.find_datacenter_by_name(
                datacenter_name=datacenter_name)
        self._datastore = self.find_datastore_by_name(
            datastore_name, datacenter=self.datacenter)
        self._fd = open(self.params.get('source'), 'rb')
        self._data = mmap.mmap(self._fd.fileno(), 0, access=mmap.ACCESS_READ)
        atexit.register(self._data.close)
        atexit.register(self._fd.close)
        # maintain a failure history while going through all the hosts
        self._history = []

    @property
    def data(self):
        ''' Returns the actual data to be uploaded. '''
        return self._data

    @property
    def datacenter(self):
        ''' Returns the Datacenter managed object. '''
        return self._datacenter

    @property
    def datastore(self):
        ''' Returns the Datastore managed object. '''
        return self._datastore

    @property
    def debounce(self):
        ''' Returns true if the upload should be debounced. '''
        return self.params['debounce'] != 'none'

    @property
    def debounce_cache_local(self):
        ''' Returns true if the local file hash should be persisted. '''
        return self.params['debounce'] == 'hashcache'

    @property
    def destination_path(self):
        ''' Returns the destination path parameter '''
        return self.params['destination']

    @property
    def destination_sha256_path(self):
        ''' Returns the destination path to the sha256 file '''
        return self.destination_path + '.sha256'

    @property
    def source_path(self):
        ''' Returns the source path parameter '''
        return self.params['source']

    @property
    def source_sha256_path(self):
        ''' Returns the source path to the sha256 file '''
        return self.source_path + '.sha256'

    def upload(self):
        ''' Upload.  If a host is unreachable then try another. '''
        for host_mount in self.datastore.host:
            try:
                self._esxi = host_mount.key
                if self.debounce:
                    same, hash = self._destination_exists()
                    if same:
                        self.module.exit_json(
                            changed=False,
                            msg="File '{0}' already exists at '[{1}] {2}'.".format(
                                self.source_path, self.datastore.name,
                                self.destination_path))
                self._put(self.destination_path, self.data)
                if self.debounce:
                    self._put(self.destination_sha256_path, hash)
                self.module.exit_json(
                    changed=True,
                    msg="File '{0}' uploaded to '[{1}] {2}' through host {3}."
                        .format(self.source_path, self.datastore.name,
                                self.destination_path, self._esxi.name))
            except Exception as e:
                self._history.append(to_native(e))
        self.module.fail_json(msg='Unable to upload.', reason=self._history)

    def _destination_exists(self):
        '''
            Check to see if the file already exists and has a corresponding
            .sha256 file on the destination.  If so, this operation can be
            idempotent by reading the .sha256 file, and calculating the local
            SHA256, and if they match then there is nothing to do.

            Returns:
                ( same, hash )
        '''
        local_hash = self._local_hash()
        self.module.debug('LOCAL  SHA256: ' + local_hash)
        remote_hash = self._remote_hash()
        self.module.debug('REMOTE SHA256: ' + str(remote_hash))
        return (local_hash == remote_hash, local_hash)

    def _get(self, url, headers=None):
        ''' Issue a GET - on 404 response return is None otherwise text '''
        resp, info = fetch_url(self.module, url, headers=headers,
                               method='GET')
        status_code = info['status']
        if status_code == 404:
            return None
        if status_code == 200:
            return resp.read()
        raise Exception("during get '{0}' unexpected response {1}: {2}"
                        .format(url, status_code, info))

    def _local_hash(self):
        ''' Obtain and optionally cache the local hash. '''
        generate_sha256 = True
        if self.debounce_cache_local:
            # we regenerate the hash if the .sha256 file is
            # older than the source
            source_stat = os.stat(self.source_path)
            if os.path.exists(self.source_sha256_path):
                sha256_stat = os.stat(self.source_sha256_path)
                generate_sha256 = source_stat.st_mtime >= sha256_stat.st_mtime
        if generate_sha256:
            hash = hashlib.sha256(self.data).hexdigest()
            if self.debounce_cache_local:
                with open(self.source_sha256_path, "w") as file:
                    file.write(hash)
            return hash
        with open(self.source_sha256_path, "r") as file:
            return file.read()

    def _put(self, dest, data):
        ''' Perform an upload. '''
        url = self._vmware_datastore_io_url(dest)
        ticket = self.acquire_service_ticket(url, 'PUT')
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(data)),
            "Cookie": 'vmware_cgi_ticket=' + ticket.id
        }
        resp, info = fetch_url(self.module, url, data=data,
                               headers=headers, method='PUT')
        status_code = info['status']
        if status_code not in (200, 201):
            raise Exception(
                "Failed to upload file '{0}' to '{1}': status code {2}: {3}"
                .format(self.source_path, self.destination_path,
                        status_code, info))

    def _remote_hash(self):
        '''
            Read the <destination>.sha256 file if it exists on the server.
            If it does not exist then return None
        '''
        url = self._vmware_datastore_io_url(self.destination_sha256_path)
        ticket = self.acquire_service_ticket(url, 'GET')
        headers = {'Cookie': 'vmware_cgi_ticket=' + ticket.id}
        return self._get(url, headers=headers)

    def _vmware_datastore_io_url(self, destpath):
        ''' Constructs a safe URL that ESXi accepts reliably. '''
        params = {'dsName': self.datastore.name}
        return 'https://{0}/folder/{1}?{2}'.format(
            self._esxi.name,
            urllib_parse.quote(destpath.strip('/')),
            urllib_parse.urlencode(params))


def main():
    spec = vmware_argument_spec()
    spec.update(dict(
        datacenter=dict(type='str', required=False, aliases=['datacenter_name']),
        datastore=dict(type='str', required=True, aliases=['datastore_name']),
        source=dict(type='str', required=True),
        destination=dict(type='str', required=True),
        debounce=dict(type='str', choices=['none', 'hash', 'hashcache'], default='none')
    ))

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    datastore_upload_mgr = VmwareDatastoreUploadMgr(module=module)
    datastore_upload_mgr.upload()


if __name__ == '__main__':
    main()

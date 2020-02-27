#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Anton Bayandin (@aneroid13)
# Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0.html)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_ova
short_description: Upload and download ova templates from VMware vSphere
description:
    - This module can be used to add and delete datastore cluster in given VMware environment.
    - All parameters and VMware object values are case sensitive.
author:
-  Anton Bayandin (@aneroid13)
-  Module based on community pyvmomi samples (https://github.com/vmware/pyvmomi-community-samples/tree/master/samples)
notes:
    - Tested on vSphere 6.0, 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    action:
      description:
      - Performed Action - download or upload ova/ovf file
      - Script check existence of vm on upload. For existing vm it count vm uploaded already. 
      choices: [ download, upload ]
      required: True
    path:
      description:
      - Path to get or save ova/ovf file.
      required: True
    name:
      description:
      - On donload: Name of vm or template to download like ova file.
      - On upload: Name of the file (ova/ovf) without extension.
      required: True
    type:
      description:
      - Type of file you work with.
      choices: [ ova, ovf ]
      default: ova
    vc_path:
      description:
      - Folders path in VMware vSphere for upload.
      aliases: [folder]
    dc:
      description:
      - Name of datacenter for upload.
      aliases: [datacenter]
    ds: 
      description:
      - Name of datastore for upload.
      aliases: [datastore]
    rp:
      description:
      - Name of resouce pool for upload. 
      - Can be name of resource pool or name of compute cluster.
      aliases: [resourcepool, resource_pool]
    new_name:
      description:
      - New name for uploaded virtual machine.
    new_net:
      description:
      - New network mapping for uploaded virtual machine. 
      - When new_net omitted, you can get 'Host did not have any virtual network defined' error, 
      if you download and upload vm between different vCenters(with different networks).
      aliases: [new_network]
    nvram:
      description:
      - Forms and download ovf/ova file with nvram file.
      - Vmware changed .ovf format in VSphere 6.7 version. New version contains .nvram file with EFI firmware.
      - VMware community discussion here https://communities.vmware.com/thread/596814
      - .ovf files exported by any vmware tool from vcenter 6.7, compatible with vCenter 6.7 and newer versions only !! 
      default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        validate_certs: False
        port: 443
        action: upload
        type: ova
        name: tmp_test-db1
        path: '/data/tmp/'
        vc_path: 'Testzone/_Templates'
        dc: 'DC-1'
        ds: 'DC-01-VT'
        rp: 'RP-DB' # Can be cluster or resource pool name
        
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        validate_certs: False
        port: 443
        action: upload
        type: ova
        name: '{{ inventory_hostname }}'
        path: '/data/tmp/'
        vc_path: 'Testzone/_Templates'
        dc: 'DC-1'
        ds: 'DC-01-VT'
        rp: 'RP-DB' # Can be cluster or resource pool name
        new_name: 'test-db2'
        new_net: 'DB_Test_Network'
        
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        validate_certs: False
        port: 443
        action: download
        type: ovf
        name: 'tmp_test-db1'
        path: '/data/tmp/'
'''

RETURN = ''' # '''

from __future__ import absolute_import, division, print_function
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

import time, os, tarfile, random, threading, requests, urllib3
from lxml import etree
from io import BytesIO
from Queue import Queue
from ansible.module_utils import basic
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, find_object_by_name, find_network_by_name)

# Disable TLS error warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FileHandle:
    def __init__(self, filename):
        self.filename = filename
        self.fh = open(filename, 'rb')

        self.st_size = os.stat(filename).st_size
        self.offset = 0

    def __del__(self):
        self.fh.close()

    def size(self):
        return self.st_size

    def tell(self):
        return self.fh.tell()

    def get_file(self):
        return self.fh

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset

        return self.fh.seek(offset, whence)

    def seekable(self):
        return True

    def read(self, amount):
        self.offset += amount
        result = self.fh.read(amount)
        return result

    # A slightly more accurate percentage
    def progress(self):
        return int(100.0 * self.offset / self.st_size)


class WebHandle:
    def __init__(self, url):
        self.url = url
        r = requests.get(self.url, verify=False)
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        if 'accept-ranges' not in r.headers:
            raise Exception("Site does not accept ranges")
        self.st_size = int(r.headers.get('content-length'))
        self.offset = 0

    def size(self):
        return self.st_size

    def tell(self):
        return self.offset

    def get_file(self):
        return r

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset
        return self.offset

    def seekable(self):
        return True

    def read(self, amount):
        start = self.offset
        end = self.offset + amount - 1
        header = {'Range': 'bytes={s}-{e}'.format(s=start, e=end)}
        with requests.get(self.url, headers=header, verify=False, stream=True) as r:
            result = r.raw.read(amount)
        self.offset += amount
        return result

    # A slightly more accurate percentage
    def progress(self):
        return int(100.0 * self.offset / self.st_size)


class OvfUploadHandler(object):
    """
    OvfHandler handles most of the OVA operations.
    It processes the tarfile, matches disk keys to files and
    uploads the disks, while keeping the progress up to date for the lease.
    """

    def __init__(self, infile, module, file_type):
        """
        Performs necessary initialization, opening the OVA file,
        processing the files and reading the embedded ovf file.
        """
        self.module = module
        self.spec = None
        self.lease = None
        self.file_type = file_type
        self.handle = self._create_file_handle(infile)
        self.workpath = os.path.dirname(infile)
        if self.file_type == 'ova':
            self.tarfile = tarfile.open(fileobj=self.handle)
            ovffilename = list(filter(lambda x: x.endswith(".ovf"), self.tarfile.getnames()))[0]
            ovffile = self.tarfile.extractfile(ovffilename)
            self.descriptor = ovffile.read().decode()
        elif self.file_type == 'ovf':
            self.descriptor = self.handle.read(self.handle.size()).decode()

    def _create_file_handle(self, entry):
        """
        A simple mechanism to pick whether the file is local or not. This is not very robust.
        """
        if os.path.exists(entry):
            return FileHandle(entry)
        else:
            return WebHandle(entry)

    def get_descriptor(self):
        return self.descriptor

    def set_spec(self, spec):
        """
        The import spec is needed for later matching disks keys with file names.
        """
        self.spec = spec

    def get_tarfile_size(self, tar_file):
        """
        Determine the size of a file inside the tarball.
        If the object has a size attribute, use that. Otherwise seek to the end
        and report that.
        """
        if hasattr(tar_file, 'size'):
            return tar_file.size
        size = tar_file.seek(0, 2)
        tar_file.seek(0, 0)
        return size

    def get_tar_disk(self, file_item, lease):
        """
        Does translation for disk key to file name, returning a file handle.
        """
        ovffilename = list(filter(lambda x: x == file_item.path, self.tarfile.getnames()))[0]
        return self.tarfile.extractfile(ovffilename)

    def get_device_url(self, file_item, lease):
        for deviceUrl in lease.info.deviceUrl:
            if deviceUrl.importKey == file_item.deviceId:
                return deviceUrl
        self.module.fail_json(msg="Failed to find deviceUrl for file %s" % file_item.path)

    def upload_disks(self, lease, host):
        """
        Uploads all the disks, with a progress keep-alive.
        """
        self.lease = lease
        try:
            self.start_timer()
            for file_item in self.spec.fileItem:
                self.upload_disk(file_item, lease, host)
            lease.Complete()
            # Finished deploy successfully.
            return 0
        except vmodl.MethodFault as e:
            lease.Abort(e)
            self.module.fail_json(msg="Hit an error in upload: %s" % e)
        except Exception as e:
            lease.Abort(vmodl.fault.SystemError(reason=str(e)))
            self.module.fail_json(msg="Lease: {}, hit an error in upload: {}".format(lease.info, e))

    def upload_disk(self, file_item, lease, host):
        """
        Upload an individual disk. Passes the file handle of the disk directly to the urlopen request.
        """
        upload_file = headers = None
        if self.file_type == 'ova':
            upload_file = self.get_tar_disk(file_item, lease)
            if upload_file is None:
                return
            headers = {'Content-length': str(self.get_tarfile_size(upload_file))}
        elif self.file_type == 'ovf':
            file_handle = self._create_file_handle(os.path.join(self.workpath, file_item.path))
            if file_handle is None:
                return
            upload_file = file_handle.get_file()
            headers = {'Content-length': str(file_handle.size())}

        device_url = self.get_device_url(file_item, lease)
        url = device_url.url.replace('*', host)
        requests.post(url, headers=headers, data=upload_file, verify=False)

    def start_timer(self):
        """
        A simple way to keep updating progress while the disks are transferred.
        """
        threading.Timer(5, self.timer).start()

    def timer(self):
        """
        Update the progress and reschedule the timer if not complete.
        """
        try:
            prog = self.handle.progress()
            self.lease.Progress(prog)
            if self.lease.state not in [vim.HttpNfcLease.State.done, vim.HttpNfcLease.State.error]:
                self.start_timer()
        except Exception as ex:  # Any exception means we should stop updating progress.
            pass


class OvfUploader(PyVmomi):
    def __init__(self, module):
        super(OvfUploader, self).__init__(module)
        self.vm_name = module.params['name']
        self.file_type = module.params['type']
        self.hostname = module.params['hostname']
        self.new_name = module.params['new_name']
        self.path = module.params['path']
        filename = str(module.params['name'] + "." + module.params['type'])
        self.full_path = os.path.join(self.path, filename)
        self.vc_path = module.params['vc_path']
        self.folder = None
        self.dc = None
        self.ds = None
        self.rp = None
        self.new_net = None

    def search_vm(self):
        vm_obj = self.get_vm_or_template(self.vm_name)
        return vm_obj

    def find_path(self, path=""):
        lpath = path.split("/")
        container = self.content.viewManager.CreateInventoryView()

        container.OpenFolder([container.view[0]])  # get VC root
        vm_folder = [obj for obj in container.view if obj.name == 'vm' and type(obj) == vim.Folder]
        container.OpenFolder(vm_folder)  # get root folder

        nf = 0
        folder = None
        while nf <= len(lpath) - 1:
            folder = [obj for obj in container.view if obj.name == lpath[nf]]
            if not folder:
                raise NameError("No such folder: {}".format(lpath[nf]))
            container.OpenFolder(folder)
            nf += 1

        container.Destroy()

        return folder[0]

    def get_ovf_networks(self, xml):
        ovf_nets = []

        it = etree.iterparse(BytesIO(xml.encode('utf-8')))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split("}")[1][0:]

        root = it.root

        for ovf_nw in root.findall('./NetworkSection/Network'):
            for att_key, att_vol in ovf_nw.attrib.items():
                att_key = att_key.split("}")[1][0:]
                if att_key == 'name':
                    ovf_nets.append(att_vol)

        return ovf_nets

    def get_vc_objects(self):
        dc_name = self.module.params['dc']  # Datacenter
        ds_name = self.module.params['ds']  # Datastore
        rp_name = self.module.params['rp']  # Resource pool
        new_net = self.module.params['new_net']  # Network

        self.dc = self.find_datacenter_by_name(dc_name)
        self.ds = self.find_datastore_by_name(ds_name)
        if new_net:
            self.new_net = find_network_by_name(self.content, new_net)

        rp = find_object_by_name(self.content, rp_name, [vim.ResourcePool])
        cl = find_object_by_name(self.content, rp_name, [vim.ClusterComputeResource])
        if cl is not None:
            self.rp = cl.resourcePool
        elif rp is not None:
            self.rp = rp

        if not self.dc:
            self.module.fail_json(
                msg="No such datacenter {dc} in {vc}".format(dc=dc_name, vc=self.module.params['hostname']))

        if not self.ds:
            self.module.fail_json(
                msg="No such datastore {ds} in {vc}".format(ds=ds_name, vc=self.module.params['hostname']))

        if not self.rp:
            self.module.fail_json(msg="No such resource pool or cluster {rp} in {vc}".format(rp=rp_name,
                                                                                vc=self.module.params['hostname']))
        try:
            self.folder = self.find_path(self.vc_path)
        except NameError as e:
            self.module.fail_json(msg=str(e.message))

    def upload(self):
        self.get_vc_objects()
        ovf_handle = OvfUploadHandler(self.full_path, self.module, self.file_type)
        ovf_manager = self.content.ovfManager

        rnd_host = random.choice(self.rp.owner.host)
        vhp = vim.OvfManager.ValidateHostParams()
        hv = ovf_manager.ValidateHost(ovf_handle.get_descriptor(), rnd_host, vhp)
        if hv.error:
            errormsg = ""
            for each in hv.error:
                errormsg += each.msg + "; "
            self.module.fail_json(msg="The OVA/OVF file can't be validated by {ho} host: {err} ".format(ho=rnd_host, err=errormsg))

        # CreateImportSpecParams can specify many useful things such:
        # - diskProvisioning (thin/thick/sparse/etc)
        # - networkMapping (to map to networks)
        # - propertyMapping (descriptor specific properties)
        cisp = vim.OvfManager.CreateImportSpecParams()

        if self.new_net:
            ovf_nw = self.get_ovf_networks(ovf_handle.get_descriptor())
            cisp.networkMapping = []
            for nw in ovf_nw:
                cisp.networkMapping.append(
                    vim.OvfManager.NetworkMapping(name=nw, network=self.new_net)
                )
        if self.new_name:
            cisp.entityName = self.new_name

        cisr = ovf_manager.CreateImportSpec(ovf_handle.get_descriptor(), self.rp, self.ds, cisp)

        # These errors might be handleable by supporting the parameters in CreateImportSpecParams
        if len(cisr.error):
            for error in cisr.error:
                self.module.fail_json(msg="The following errors will prevent import of this OVA/OVF: {} ".format(error))

        ovf_handle.set_spec(cisr)

        lease = self.rp.ImportVApp(cisr.importSpec, self.folder)
        while lease.state == vim.HttpNfcLease.State.initializing:
            time.sleep(1)

        if lease.state == vim.HttpNfcLease.State.error:
            self.module.fail_json(msg="Lease error: {}".format(lease.error))
        if lease.state == vim.HttpNfcLease.State.done:
            return {'changed': False, 'failed': False}

        if ovf_handle.upload_disks(lease, self.hostname) == 0:
            return {'changed': True, 'failed': False}


class LeaseProgressUpdater(threading.Thread):
    """
        Lease Progress Updater & keep alive thread
    """

    def __init__(self, http_nfc_lease, total_bytes, update_interval):
        threading.Thread.__init__(self)
        self._running = True
        self.httpNfcLease = http_nfc_lease
        self.updateInterval = update_interval
        self.progressPercent = 0
        self.httpNfcLease.HttpNfcLeaseProgress(0)
        self.qu = Queue()
        self.received_bytes = 0
        self.total_bytes = total_bytes

    def finish(self):
        self.httpNfcLease.HttpNfcLeaseProgress(100)
        self.httpNfcLease.HttpNfcLeaseComplete()
        self.stop()

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                if self.httpNfcLease.state == vim.HttpNfcLease.State.done:
                    return

                qsize = self.qu.qsize()
                if qsize:
                    for i in range(qsize):
                        self.received_bytes += self.qu.get()

                self.progressPercent = int((self.received_bytes / self.total_bytes) * 100)

                self.httpNfcLease.HttpNfcLeaseProgress(self.progressPercent)
                time.sleep(self.updateInterval)
            except Exception as ex:
                print(ex.message)
                return


class DownloaderTh(threading.Thread):

    def __init__(self, queue, cookies, url, vmdk_file):
        threading.Thread.__init__(self)
        self._running = True
        self.queue = queue
        self.cookies = cookies
        self.url = url
        self.vmdk_file = vmdk_file
        self.bytes_receive_delta = 0
        self.done = False

    def start_timer(self):
        threading.Timer(3, self.sent_info).start()

    def sent_info(self):
        self.queue.put(self.bytes_receive_delta)
        self.bytes_receive_delta = 0
        if not self.done:
            self.start_timer()

    def disk_downloading(self):
        with open(self.vmdk_file, 'wb') as handle:
            headers = {'Accept': 'application/x-vnd.vmware-streamVmdk'}
            response = requests.get(self.url, headers=headers, stream=True, cookies=self.cookies, verify=False)

            if not response.ok:  # response other than 200
                response.raise_for_status()

            for block in response.iter_content(chunk_size=4096):
                # filter out keep-alive new chunks
                if block:
                    handle.write(block)
                    self.bytes_receive_delta += len(block)
        self.done = True

    def stop(self):
        self._running = False

    def run(self):
        self.start_timer()
        self.disk_downloading()


class OvfDownloadHelper(object):
    def __init__(self, vname, lease, cookie, vm_path, vm_file_size, module, nvram):
        self.vm_name = vname
        self.module = module
        self.path = vm_path
        self.ovf_files = []
        self.cookie = self._make_cookie(cookie)
        self.disk_treads = []
        self.nvram = nvram
        # self.headers = {'Accept': 'application/x-vnd.vmware-streamVmdk'}

        # starting lease updater
        self.lease_updater = LeaseProgressUpdater(lease, vm_file_size, 20)
        self.lease_updater.start()

    def lease_finished(self):
        self.lease_updater.finish()

    def _make_cookie(self, l_cookie):
        cookie_a = l_cookie.split(';')
        cookie_name = cookie_a[0].split('=')[0]
        cookie_text = ' {0}; ${1}'.format(cookie_a[0].split('=')[1], cookie_a[1].lstrip())
        return {cookie_name: cookie_text}

    def create_empty_disk_file(self, disk_filename):
        disk_file = os.path.join(self.path, self.vm_name + "-" + disk_filename)
        try:
            fp = open(disk_file, "wb")
            fp.close()
        except Exception as ex:
            self.module.fail_json(msg="Error to create disk file {}: {}".format(disk_file, ex.message))
        return disk_file

    def create_empty_nvram_file(self):
        disk_file = os.path.join(self.path, self.vm_name + ".nvram")
        try:
            fp = open(disk_file, "wb")
            fp.close()
        except Exception as ex:
            self.module.fail_json(msg="Error to create disk file {}: {}".format(disk_file, ex.message))
        return disk_file

    def get_devices(self, devices_url):
        for device_url in devices_url:
            if device_url.disk:
                self.get_device(device_url)
            elif self.nvram and "nvram" in device_url.key:
                self.get_device(device_url)
            else:
                continue  # "Device is not eligible for export. This could be a mounted iso or img."

        while self.disk_treads:
            time.sleep(2)
            self.disk_treads = [th for th in self.disk_treads if th.is_alive()]

        # Adding Disk to OVF Files list
        for dev_url in devices_url:
            if dev_url.disk:
                file_path = os.path.join(self.path, str(self.vm_name) + "-" + str(dev_url.targetId))
                ovf_file = vim.OvfManager.OvfFile()
                ovf_file.deviceId = dev_url.key
                ovf_file.path = str(self.vm_name) + "-" + str(dev_url.targetId)
                ovf_file.size = os.path.getsize(file_path)
                self.ovf_files.append(ovf_file)
            elif self.nvram and "nvram" in dev_url.key:
                file_path = os.path.join(self.path, self.vm_name + ".nvram")
                ovf_file = vim.OvfManager.OvfFile()
                ovf_file.deviceId = dev_url.key
                ovf_file.path = self.vm_name + ".nvram"
                ovf_file.size = os.path.getsize(file_path)
                self.ovf_files.append(ovf_file)

    def get_device(self, dev_url):
        if dev_url.disk:
            empty_file = self.create_empty_disk_file(dev_url.targetId)
        else:
            if "nvram" in dev_url.key:
                empty_file = self.create_empty_nvram_file()
        disk_down = DownloaderTh(self.lease_updater.qu, self.cookie, dev_url.url, empty_file)
        disk_down.start()
        self.disk_treads.append(disk_down)

    def create_ovf(self, vm_obj, ovf_manager):
        ovf_parameters = vim.OvfManager.CreateDescriptorParams()
        ovf_parameters.name = vm_obj.name
        ovf_parameters.ovfFiles = self.ovf_files
        vm_descriptor_result = ovf_manager.CreateDescriptor(obj=vm_obj, cdp=ovf_parameters)
        if vm_descriptor_result.error:
            raise vm_descriptor_result.error[0].fault
        else:
            ovf_descriptor_path = os.path.join(self.path, vm_obj.name + '.ovf')
            with open(ovf_descriptor_path, 'wb') as handle:
                handle.write(vm_descriptor_result.ovfDescriptor)


class OvfDownloader(PyVmomi):
    def __init__(self, module):
        super(OvfDownloader, self).__init__(module)
        self.vm_name = module.params['name']
        self.workdir = module.params['path']
        self.nvram = module.params['nvram']
        self.file_type = module.params['type']

    def file_exist(self):
        fpath = None
        if self.file_type == 'ova':
            fpath = os.path.join(self.workdir, self.vm_name + "." + self.file_type)
        elif self.file_type == 'ovf':
            fpath = os.path.join(self.workdir, self.vm_name, self.vm_name + "." + self.file_type)
        return os.path.exists(fpath)

    def search_vm(self):
        vm_obj = self.get_vm_or_template(self.vm_name)
        return vm_obj

    def check_dir(self, vm_id):
        try:
            if not os.path.isdir(self.workdir):
                os.mkdir(self.workdir)

            target_directory = os.path.join(self.workdir, vm_id)
            if not os.path.isdir(target_directory):
                os.mkdir(target_directory)

            return target_directory
        except Exception as ex:
            self.module.fail_json(msg=str(ex))

    def tar_it(self, vmdir):
        ovf_file = [ovf for ovf in os.listdir(vmdir) if ovf[-4:] == ".ovf"][0]
        vmdk_files = [vmdk for vmdk in os.listdir(vmdir) if vmdk[-5:] == ".vmdk"]
        ova_file = os.path.join(self.workdir, self.vm_name + ".ova")
        if self.nvram:
            nvram_file = [nvram for nvram in os.listdir(vmdir) if nvram[-6:] == ".nvram"][0]

        try:
            with tarfile.open(ova_file, mode='w') as tar:
                tar.add(os.path.join(vmdir, ovf_file), arcname=ovf_file)
                if self.nvram:
                    tar.add(os.path.join(vmdir, nvram_file), arcname=nvram_file)
                for vmdk in vmdk_files:
                    tar.add(os.path.join(vmdir, vmdk), arcname=vmdk)
        except Exception as ex:
            self.module.fail_json(msg="Cannot create .ova file.")

        try:
            for file in os.listdir(vmdir):
                os.remove(os.path.join(vmdir, file))
            os.removedirs(vmdir)
        except Exception as ex:
            self.module.fail_json(msg="Cannot clean temp dir {}".format(vmdir))

    def download(self, vm_obj):
        # Create Header and Cookies
        cookie_stub = self.content.searchIndex._stub.cookie
        vm_dir = self.check_dir(vm_obj.config.instanceUuid)
        vm_file_size = vm_obj.summary.storage.unshared
        http_nfc_lease = vm_obj.ExportVm()  # Getting HTTP NFC Lease
        ovf_handle = OvfDownloadHelper(vm_obj.name, http_nfc_lease, cookie_stub, vm_dir, vm_file_size, self.module, self.nvram)

        while http_nfc_lease.state == vim.HttpNfcLease.State.initializing:
            time.sleep(0.2)

        if http_nfc_lease.state == vim.HttpNfcLease.State.error:
            self.module.fail_json(msg="HTTP NFC Lease error: {}".format(http_nfc_lease.state.error))
        elif http_nfc_lease.state == vim.HttpNfcLease.State.ready:
            ovf_handle.get_devices(http_nfc_lease.info.deviceUrl)

        ovf_handle.create_ovf(vm_obj, self.content.ovfManager)
        ovf_handle.lease_finished()

        if self.file_type == 'ova':
            self.tar_it(vm_dir)
        else:
            os.rename(vm_dir, os.path.join(self.workdir, vm_obj.name))

        return {'changed': True, 'failed': False}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        action=dict(type='str', required=True,
                    choices=['upload', 'download']),
        name=dict(type='str', required=True),
        type=dict(type='str', default='ova',
                  choices=['ova', 'ovf']),
        path=dict(type='str', required=True),
        vc_path=dict(type='str', aliases=['folder']),
        dc=dict(type='str', aliases=['datacenter']),
        ds=dict(type='str', aliases=['datastore']),
        rp=dict(type='str', aliases=['resourcepool', 'resource_pool']),
        nvram=dict(type='bool', default=False),
        new_name=dict(type='str'),
        new_net=dict(type='str', aliases=['new_network'])
    )

    module = AnsibleModule(argument_spec=argument_spec)
    result = {'failed': False, 'changed': False}

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    if module.params['action'] == 'download':
        ovf_down = OvfDownloader(module)
        if not ovf_down.file_exist():
            get_smth = ovf_down.search_vm()
            if get_smth is None:
                module.fail_json(msg="Can't find VM {}".format(module.params['name']))
            elif get_smth.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
                module.fail_json(msg="VM {} must be powered off".format(module.params['name']))
            else:
                result = ovf_down.download(get_smth)

    if module.params['action'] == 'upload':
        ovf_up = OvfUploader(module)
        if not ovf_up.search_vm():
            result = ovf_up.upload()

    module.exit_json(**result)


if __name__ == '__main__':
    main()

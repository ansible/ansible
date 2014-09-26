#!/usr/bin/python

# (c) 2013, Paul Durivage <paul.durivage@rackspace.com>
#
# This file is part of Ansible.
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

# This is a DOCUMENTATION stub specific to this module, it extends
# a documentation fragment located in ansible.utils.module_docs_fragments
DOCUMENTATION = '''
---
module: rax_files_objects
short_description: Upload, download, and delete objects in Rackspace Cloud Files
description:
  - Upload, download, and delete objects in Rackspace Cloud Files
version_added: "1.5"
options:
  clear_meta:
    description:
      - Optionally clear existing metadata when applying metadata to existing objects.
        Selecting this option is only appropriate when setting type=meta
    choices:
      - "yes"
      - "no"
    default: "no"
  container:
    description:
      - The container to use for file object operations.
    required: true
    default: null
  dest:
    description:
      - The destination of a "get" operation; i.e. a local directory, "/home/user/myfolder".
        Used to specify the destination of an operation on a remote object; i.e. a file name,
        "file1", or a comma-separated list of remote objects, "file1,file2,file17"
  expires:
    description:
      - Used to set an expiration on a file or folder uploaded to Cloud Files.
        Requires an integer, specifying expiration in seconds
    default: null
  meta:
    description:
      - A hash of items to set as metadata values on an uploaded file or folder
    default: null
  method:
    description:
      - The method of operation to be performed.  For example, put to upload files
        to Cloud Files, get to download files from Cloud Files or delete to delete
        remote objects in Cloud Files
    choices:
      - get
      - put
      - delete
    default: get
  src:
    description:
      - Source from which to upload files.  Used to specify a remote object as a source for
        an operation, i.e. a file name, "file1", or a comma-separated list of remote objects,
        "file1,file2,file17".  src and dest are mutually exclusive on remote-only object operations
    default: null
  structure:
    description:
      - Used to specify whether to maintain nested directory structure when downloading objects
        from Cloud Files.  Setting to false downloads the contents of a container to a single,
        flat directory
    choices:
      - yes
      - "no"
    default: "yes"
  state:
    description:
      - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
  type:
    description:
      - Type of object to do work on
      - Metadata object or a file object
    choices:
      - file
      - meta
    default: file
author: Paul Durivage
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: "Test Cloud Files Objects"
  hosts: local
  gather_facts: False
  tasks:
    - name: "Get objects from test container"
      rax_files_objects: container=testcont dest=~/Downloads/testcont

    - name: "Get single object from test container"
      rax_files_objects: container=testcont src=file1 dest=~/Downloads/testcont

    - name: "Get several objects from test container"
      rax_files_objects: container=testcont src=file1,file2,file3 dest=~/Downloads/testcont

    - name: "Delete one object in test container"
      rax_files_objects: container=testcont method=delete dest=file1

    - name: "Delete several objects in test container"
      rax_files_objects: container=testcont method=delete dest=file2,file3,file4

    - name: "Delete all objects in test container"
      rax_files_objects: container=testcont method=delete

    - name: "Upload all files to test container"
      rax_files_objects: container=testcont method=put src=~/Downloads/onehundred

    - name: "Upload one file to test container"
      rax_files_objects: container=testcont method=put src=~/Downloads/testcont/file1

    - name: "Upload one file to test container with metadata"
      rax_files_objects:
        container: testcont
        src: ~/Downloads/testcont/file2
        method: put
        meta:
          testkey: testdata
          who_uploaded_this: someuser@example.com

    - name: "Upload one file to test container with TTL of 60 seconds"
      rax_files_objects: container=testcont method=put src=~/Downloads/testcont/file3 expires=60

    - name: "Attempt to get remote object that does not exist"
      rax_files_objects: container=testcont method=get src=FileThatDoesNotExist.jpg dest=~/Downloads/testcont
      ignore_errors: yes

    - name: "Attempt to delete remote object that does not exist"
      rax_files_objects: container=testcont method=delete dest=FileThatDoesNotExist.jpg
      ignore_errors: yes

- name: "Test Cloud Files Objects Metadata"
  hosts: local
  gather_facts: false
  tasks:
    - name: "Get metadata on one object"
      rax_files_objects:  container=testcont type=meta dest=file2

    - name: "Get metadata on several objects"
      rax_files_objects:  container=testcont type=meta src=file2,file1

    - name: "Set metadata on an object"
      rax_files_objects:
        container: testcont
        type: meta
        dest: file17
        method: put
        meta:
          key1: value1
          key2: value2
        clear_meta: true

    - name: "Verify metadata is set"
      rax_files_objects:  container=testcont type=meta src=file17

    - name: "Delete metadata"
      rax_files_objects:
        container: testcont
        type: meta
        dest: file17
        method: delete
        meta:
          key1: ''
          key2: ''

    - name: "Get metadata on all objects"
      rax_files_objects:  container=testcont type=meta
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

EXIT_DICT = dict(success=False)
META_PREFIX = 'x-object-meta-'


def _get_container(module, cf, container):
    try:
        return cf.get_container(container)
    except pyrax.exc.NoSuchContainer, e:
        module.fail_json(msg=e.message)


def upload(module, cf, container, src, dest, meta, expires):
    """ Uploads a single object or a folder to Cloud Files Optionally sets an
    metadata, TTL value (expires), or Content-Disposition and Content-Encoding
    headers.
    """
    c = _get_container(module, cf, container)

    num_objs_before = len(c.get_object_names())

    if not src:
        module.fail_json(msg='src must be specified when uploading')

    src = os.path.abspath(os.path.expanduser(src))
    is_dir = os.path.isdir(src)

    if not is_dir and not os.path.isfile(src) or not os.path.exists(src):
        module.fail_json(msg='src must be a file or a directory')
    if dest and is_dir:
        module.fail_json(msg='dest cannot be set when whole '
                             'directories are uploaded')

    cont_obj = None
    if dest and not is_dir:
        try:
            cont_obj = c.upload_file(src, obj_name=dest, ttl=expires)
        except Exception, e:
            module.fail_json(msg=e.message)
    elif is_dir:
        try:
            id, total_bytes = cf.upload_folder(src, container=c.name, ttl=expires)
        except Exception, e:
            module.fail_json(msg=e.message)

        while True:
            bytes = cf.get_uploaded(id)
            if bytes == total_bytes:
                break
            time.sleep(1)
    else:
        try:
            cont_obj = c.upload_file(src, ttl=expires)
        except Exception, e:
            module.fail_json(msg=e.message)

    num_objs_after = len(c.get_object_names())

    if not meta:
        meta = dict()

    meta_result = dict()
    if meta:
        if cont_obj:
            meta_result = cont_obj.set_metadata(meta)
        else:
            def _set_meta(objs, meta):
                """ Sets metadata on a list of objects specified by name """
                for obj in objs:
                    try:
                        result = c.get_object(obj).set_metadata(meta)
                    except Exception, e:
                        module.fail_json(msg=e.message)
                    else:
                        meta_result[obj] = result
                return meta_result

            def _walker(objs, path, filenames):
                """ Callback func for os.path.walk  """
                prefix = ''
                if path != src:
                    prefix = path.split(src)[-1].lstrip('/')
                filenames = [os.path.join(prefix, name) for name in filenames
                             if not os.path.isdir(name)]
                objs += filenames

            _objs = []
            os.path.walk(src, _walker, _objs)
            meta_result = _set_meta(_objs, meta)

    EXIT_DICT['success'] = True
    EXIT_DICT['container'] = c.name
    EXIT_DICT['msg'] = "Uploaded %s to container: %s" % (src, c.name)
    if cont_obj or locals().get('bytes'):
        EXIT_DICT['changed'] = True
    if meta_result:
        EXIT_DICT['meta'] = dict(updated=True)

    if cont_obj:
        EXIT_DICT['bytes'] = cont_obj.total_bytes
        EXIT_DICT['etag'] = cont_obj.etag
    else:
        EXIT_DICT['bytes'] = total_bytes

    module.exit_json(**EXIT_DICT)


def download(module, cf, container, src, dest, structure):
    """ Download objects from Cloud Files to a local path specified by "dest".
    Optionally disable maintaining a directory structure by by passing a
    false value to "structure".
    """
    # Looking for an explicit destination
    if not dest:
        module.fail_json(msg='dest is a required argument when '
                             'downloading from Cloud Files')

    # Attempt to fetch the container by name
    c = _get_container(module, cf, container)

    # Accept a single object name or a comma-separated list of objs
    # If not specified, get the entire container
    if src:
        objs = src.split(',')
        objs = map(str.strip, objs)
    else:
        objs = c.get_object_names()

    dest = os.path.abspath(os.path.expanduser(dest))
    is_dir = os.path.isdir(dest)

    if not is_dir:
        module.fail_json(msg='dest must be a directory')

    results = []
    for obj in objs:
        try:
            c.download_object(obj, dest, structure=structure)
        except Exception, e:
            module.fail_json(msg=e.message)
        else:
            results.append(obj)

    len_results = len(results)
    len_objs = len(objs)

    EXIT_DICT['container'] = c.name
    EXIT_DICT['requested_downloaded'] = results
    if results:
        EXIT_DICT['changed'] = True
    if len_results == len_objs:
        EXIT_DICT['success'] = True
        EXIT_DICT['msg'] = "%s objects downloaded to %s" % (len_results, dest)
    else:
        EXIT_DICT['msg'] = "Error: only %s of %s objects were " \
                           "downloaded" % (len_results, len_objs)
    module.exit_json(**EXIT_DICT)


def delete(module, cf, container, src, dest):
    """ Delete specific objects by proving a single file name or a
    comma-separated list to src OR dest (but not both).  Omitting file name(s)
    assumes the entire container is to be deleted.
    """
    objs = None
    if src and dest:
        module.fail_json(msg="Error: ambiguous instructions; files to be deleted "
                             "have been specified on both src and dest args")
    elif dest:
        objs = dest
    else:
        objs = src

    c = _get_container(module, cf, container)

    if objs:
        objs = objs.split(',')
        objs = map(str.strip, objs)
    else:
        objs = c.get_object_names()

    num_objs = len(objs)

    results = []
    for obj in objs:
        try:
            result = c.delete_object(obj)
        except Exception, e:
            module.fail_json(msg=e.message)
        else:
            results.append(result)

    num_deleted = results.count(True)

    EXIT_DICT['container'] = c.name
    EXIT_DICT['deleted'] = num_deleted
    EXIT_DICT['requested_deleted'] = objs

    if num_deleted:
        EXIT_DICT['changed'] = True

    if num_objs == num_deleted:
        EXIT_DICT['success'] = True
        EXIT_DICT['msg'] = "%s objects deleted" % num_deleted
    else:
        EXIT_DICT['msg'] = ("Error: only %s of %s objects "
                            "deleted" % (num_deleted, num_objs))
    module.exit_json(**EXIT_DICT)


def get_meta(module, cf, container, src, dest):
    """ Get metadata for a single file, comma-separated list, or entire
    container
    """
    c = _get_container(module, cf, container)

    objs = None
    if src and dest:
        module.fail_json(msg="Error: ambiguous instructions; files to be deleted "
                             "have been specified on both src and dest args")
    elif dest:
        objs = dest
    else:
        objs = src

    if objs:
        objs = objs.split(',')
        objs = map(str.strip, objs)
    else:
        objs = c.get_object_names()

    results = dict()
    for obj in objs:
        try:
            meta = c.get_object(obj).get_metadata()
        except Exception, e:
            module.fail_json(msg=e.message)
        else:
            results[obj] = dict()
            for k, v in meta.items():
                meta_key = k.split(META_PREFIX)[-1]
                results[obj][meta_key] = v

    EXIT_DICT['container'] = c.name
    if results:
        EXIT_DICT['meta_results'] = results
        EXIT_DICT['success'] = True
    module.exit_json(**EXIT_DICT)


def put_meta(module, cf, container, src, dest, meta, clear_meta):
    """ Set metadata on a container, single file, or comma-separated list.
    Passing a true value to clear_meta clears the metadata stored in Cloud
    Files before setting the new metadata to the value of "meta".
    """
    objs = None
    if src and dest:
        module.fail_json(msg="Error: ambiguous instructions; files to set meta"
                             " have been specified on both src and dest args")
    elif dest:
        objs = dest
    else:
        objs = src

    objs = objs.split(',')
    objs = map(str.strip, objs)

    c = _get_container(module, cf, container)

    results = []
    for obj in objs:
        try:
            result = c.get_object(obj).set_metadata(meta, clear=clear_meta)
        except Exception, e:
            module.fail_json(msg=e.message)
        else:
            results.append(result)

    EXIT_DICT['container'] = c.name
    EXIT_DICT['success'] = True
    if results:
        EXIT_DICT['changed'] = True
        EXIT_DICT['num_changed'] = True
    module.exit_json(**EXIT_DICT)


def delete_meta(module, cf, container, src, dest, meta):
    """ Removes metadata keys and values specified in meta, if any.  Deletes on
    all objects specified by src or dest (but not both), if any; otherwise it
    deletes keys on all objects in the container
    """
    objs = None
    if src and dest:
        module.fail_json(msg="Error: ambiguous instructions; meta keys to be "
                             "deleted have been specified on both src and dest"
                             " args")
    elif dest:
        objs = dest
    else:
        objs = src

    objs = objs.split(',')
    objs = map(str.strip, objs)

    c = _get_container(module, cf, container)

    results = []  # Num of metadata keys removed, not objects affected
    for obj in objs:
        if meta:
            for k, v in meta.items():
                try:
                    result = c.get_object(obj).remove_metadata_key(k)
                except Exception, e:
                    module.fail_json(msg=e.message)
                else:
                    results.append(result)
        else:
            try:
                o = c.get_object(obj)
            except pyrax.exc.NoSuchObject, e:
                module.fail_json(msg=e.message)

            for k, v in o.get_metadata().items():
                try:
                    result = o.remove_metadata_key(k)
                except Exception, e:
                    module.fail_json(msg=e.message)
                results.append(result)

    EXIT_DICT['container'] = c.name
    EXIT_DICT['success'] = True
    if results:
        EXIT_DICT['changed'] = True
        EXIT_DICT['num_deleted'] = len(results)
    module.exit_json(**EXIT_DICT)


def cloudfiles(module, container, src, dest, method, typ, meta, clear_meta,
               structure, expires):
    """ Dispatch from here to work with metadata or file objects """
    cf = pyrax.cloudfiles

    if cf is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if typ == "file":
        if method == 'put':
            upload(module, cf, container, src, dest, meta, expires)

        elif method == 'get':
            download(module, cf, container, src, dest, structure)

        elif method == 'delete':
            delete(module, cf, container, src, dest)

    else:
        if method == 'get':
            get_meta(module, cf, container, src, dest)

        if method == 'put':
            put_meta(module, cf, container, src, dest, meta, clear_meta)

        if method == 'delete':
            delete_meta(module, cf, container, src, dest, meta)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            container=dict(required=True),
            src=dict(),
            dest=dict(),
            method=dict(default='get', choices=['put', 'get', 'delete']),
            type=dict(default='file', choices=['file', 'meta']),
            meta=dict(type='dict', default=dict()),
            clear_meta=dict(default=False, type='bool'),
            structure=dict(default=True, type='bool'),
            expires=dict(type='int'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    container = module.params.get('container')
    src = module.params.get('src')
    dest = module.params.get('dest')
    method = module.params.get('method')
    typ = module.params.get('type')
    meta = module.params.get('meta')
    clear_meta = module.params.get('clear_meta')
    structure = module.params.get('structure')
    expires = module.params.get('expires')

    if clear_meta and not typ == 'meta':
        module.fail_json(msg='clear_meta can only be used when setting metadata')

    setup_rax_module(module, pyrax)
    cloudfiles(module, container, src, dest, method, typ, meta, clear_meta, structure, expires)


from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

main()

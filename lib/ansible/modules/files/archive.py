#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ben Doherty <bendohmv@gmail.com>
# Sponsored by Oomph, Inc. http://www.oomphinc.com
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: archive
version_added: 2.3
short_description: Creates a compressed archive of one or more files or trees.
extends_documentation_fragment: files
description:
    - Packs an archive. It is the opposite of M(unarchive). By default, it assumes the compression source exists on the target. It will not copy the
      source file from the local system to the target before archiving. Source files can be deleted after archival by specifying I(remove=True).
options:
  path:
    description:
      - Remote absolute path, glob, or list of paths or globs for the file or files to compress or archive.
    required: true
  format:
    description:
      - The type of compression to use.
    choices: [ 'gz', 'bz2', 'zip' ]
    default: 'gz'
  dest:
    description:
      - The file name of the destination archive. This is required when C(path) refers to multiple files by either specifying a glob, a directory or
        multiple paths in a list.
    required: false
    default: null
  exclude_path:
    version_added: 2.4
    description:
      - Remote absolute path, glob, or list of paths or globs for the file or files to exclude from the archive
    required: false
  remove:
    description:
      - Remove any added source files and trees after adding to archive.
    required: false
    default: false

author: "Ben Doherty (@bendoh)"
notes:
    - requires tarfile, zipfile, gzip, and bzip2 packages on target host
    - can produce I(gzip), I(bzip2) and I(zip) compressed files or archives
'''

EXAMPLES = '''
# Compress directory /path/to/foo/ into /path/to/foo.tgz
- archive:
    path: /path/to/foo
    dest: /path/to/foo.tgz

# Compress regular file /path/to/foo into /path/to/foo.gz and remove it
- archive:
    path: /path/to/foo
    remove: True

# Create a zip archive of /path/to/foo
- archive:
    path: /path/to/foo
    format: zip

# Create a bz2 archive of multiple files, rooted at /path
- archive:
    path:
        - /path/to/foo
        - /path/wong/foo
    dest: /path/file.tar.bz2
    format: bz2

# Create a bz2 archive of a globbed path, while excluding specific dirnames - archive:
    path:
        - /path/to/foo/*
    dest: /path/file.tar.bz2
    exclude_path:
        - /path/to/foo/bar
        - /path/to/foo/baz
    format: bz2

# Create a bz2 archive of a globbed path, while excluding a glob of dirnames
    path:
        - /path/to/foo/*
    dest: /path/file.tar.bz2
    exclude_path:
        - /path/to/foo/ba*
    format: bz2
'''

RETURN = '''
state:
    description:
        The current state of the archived file.
        If 'absent', then no source files were found and the archive does not exist.
        If 'compress', then the file source file is in the compressed state.
        If 'archive', then the source file or paths are currently archived.
        If 'incomplete', then an archive was created, but not all source paths were found.
    type: string
    returned: always
missing:
    description: Any files that were missing from the source.
    type: list
    returned: success
archived:
    description: Any files that were compressed or added to the archive.
    type: list
    returned: success
arcroot:
    description: The archive root.
    type: string
    returned: always
expanded_paths:
    description: The list of matching paths from paths argument.
    type: list
    returned: always
expanded_exclude_paths:
    description: The list of matching exclude paths from the exclude_path argument.
    type: list
    returned: always
'''

import os
import re
import glob
import shutil
import gzip
import bz2
import filecmp
import zipfile
import tarfile
from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(type='list', required=True),
            format = dict(choices=['gz', 'bz2', 'zip', 'tar'], default='gz', required=False),
            dest = dict(required=False, type='path'),
            exclude_path = dict(type='list', required=False),
            remove = dict(required=False, default=False, type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    check_mode = module.check_mode
    paths = params['path']
    dest = params['dest']
    exclude_paths = params['exclude_path']
    remove = params['remove']

    expanded_paths = []
    expanded_exclude_paths = []
    format = params['format']
    globby = False
    changed = False
    state = 'absent'

    # Simple or archive file compression (inapplicable with 'zip' since it's always an archive)
    archive = False
    successes = []

    for i, path in enumerate(paths):
        path = os.path.expanduser(os.path.expandvars(path))

        # Expand any glob characters. If found, add the expanded glob to the
        # list of expanded_paths, which might be empty.
        if ('*' in path or '?' in path):
            expanded_paths = expanded_paths + glob.glob(path)
            globby = True

        # If there are no glob characters the path is added to the expanded paths
        # whether the path exists or not
        else:
            expanded_paths.append(path)

    # Only attempt to expand the exclude paths if it exists
    if exclude_paths:
        for i, exclude_path in enumerate(exclude_paths):
            exclude_path = os.path.expanduser(os.path.expandvars(exclude_path))

            # Expand any glob characters. If found, add the expanded glob to the
            # list of expanded_paths, which might be empty.
            if ('*' in exclude_path or '?' in exclude_path):
                expanded_exclude_paths = expanded_exclude_paths + glob.glob(exclude_path)

                # If there are no glob character the exclude path is added to the expanded
                # exclude paths whether the path exists or not.
            else:
                expanded_exclude_paths.append(exclude_path)

    if len(expanded_paths) == 0:
        return module.fail_json(path=', '.join(paths), expanded_paths=', '.join(expanded_paths), msg='Error, no source paths were found')

    # If we actually matched multiple files or TRIED to, then
    # treat this as a multi-file archive
    archive = globby or os.path.isdir(expanded_paths[0]) or len(expanded_paths) > 1

    # Default created file name (for single-file archives) to
    # <file>.<format>
    if not dest and not archive:
        dest = '%s.%s' % (expanded_paths[0], format)

    # Force archives to specify 'dest'
    if archive and not dest:
        module.fail_json(dest=dest, path=', '.join(paths), msg='Error, must specify "dest" when archiving multiple files or trees')

    archive_paths = []
    missing = []
    arcroot = ''

    for path in expanded_paths:
        # Use the longest common directory name among all the files
        # as the archive root path
        if arcroot == '':
            arcroot = os.path.dirname(path) + os.sep
        else:
            for i in range(len(arcroot)):
                if path[i] != arcroot[i]:
                    break

            if i < len(arcroot):
                arcroot = os.path.dirname(arcroot[0:i+1])

            arcroot += os.sep

        # Don't allow archives to be created anywhere within paths to be removed
        if remove and os.path.isdir(path) and dest.startswith(path):
            module.fail_json(path=', '.join(paths), msg='Error, created archive can not be contained in source paths when remove=True')

        if os.path.lexists(path) and path not in expanded_exclude_paths:
            archive_paths.append(path)
        else:
            missing.append(path)

    # No source files were found but the named archive exists: are we 'compress' or 'archive' now?
    if len(missing) == len(expanded_paths) and dest and os.path.exists(dest):
        # Just check the filename to know if it's an archive or simple compressed file
        if re.search(r'(\.tar|\.tar\.gz|\.tgz|.tbz2|\.tar\.bz2|\.zip)$', os.path.basename(dest), re.IGNORECASE):
            state = 'archive'
        else:
            state = 'compress'

    # Multiple files, or globbiness
    elif archive:
        if len(archive_paths) == 0:
            # No source files were found, but the archive is there.
            if os.path.lexists(dest):
                state = 'archive'
        elif len(missing) > 0:
            # SOME source files were found, but not all of them
            state = 'incomplete'

        archive = None
        size = 0
        errors = []

        if os.path.lexists(dest):
            size = os.path.getsize(dest)

        if state != 'archive':
            if check_mode:
                changed = True

            else:
                try:
                    # Slightly more difficult (and less efficient!) compression using zipfile module
                    if format == 'zip':
                        arcfile = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)

                    # Easier compression using tarfile module
                    elif format == 'gz' or format == 'bz2':
                        arcfile = tarfile.open(dest, 'w|' + format)

                    # Or plain tar archiving
                    elif format == 'tar':
                        arcfile = tarfile.open(dest, 'w')

                    match_root = re.compile('^%s' % re.escape(arcroot))
                    for path in archive_paths:
                        if os.path.isdir(path):
                            # Recurse into directories
                            for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                                if not dirpath.endswith(os.sep):
                                    dirpath += os.sep

                                for dirname in dirnames:
                                    fullpath = dirpath + dirname
                                    arcname = match_root.sub('', fullpath)

                                    try:
                                        if format == 'zip':
                                            arcfile.write(fullpath, arcname)
                                        else:
                                            arcfile.add(fullpath, arcname, recursive=False)

                                    except Exception as e:
                                        errors.append('%s: %s' % (fullpath, to_native(e)))

                                for filename in filenames:
                                    fullpath = dirpath + filename
                                    arcname = match_root.sub('', fullpath)

                                    if not filecmp.cmp(fullpath, dest):
                                        try:
                                            if format == 'zip':
                                                arcfile.write(fullpath, arcname)
                                            else:
                                                arcfile.add(fullpath, arcname, recursive=False)

                                            successes.append(fullpath)
                                        except Exception as e:
                                            errors.append('Adding %s: %s' % (path, to_native(e)))
                        else:
                            if format == 'zip':
                                arcfile.write(path, match_root.sub('', path))
                            else:
                                arcfile.add(path, match_root.sub('', path), recursive=False)

                            successes.append(path)

                except Exception as e:
                    module.fail_json(msg='Error when writing %s archive at %s: %s' % (format == 'zip' and 'zip' or ('tar.' + format), dest, to_native(e)),
                                     exception=format_exc())

                if arcfile:
                    arcfile.close()
                    state = 'archive'

                if len(errors) > 0:
                    module.fail_json(msg='Errors when writing archive at %s: %s' % (dest, '; '.join(errors)))

        if state in ['archive', 'incomplete'] and remove:
            for path in successes:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    elif not check_mode:
                        os.remove(path)
                except OSError as e:
                    errors.append(path)

            if len(errors) > 0:
                module.fail_json(dest=dest, msg='Error deleting some source files: ' + str(e), files=errors)

        # Rudimentary check: If size changed then file changed. Not perfect, but easy.
        if not check_mode and os.path.getsize(dest) != size:
            changed = True

        if len(successes) and state != 'incomplete':
            state = 'archive'

    # Simple, single-file compression
    else:
        path = expanded_paths[0]

        # No source or compressed file
        if not (os.path.exists(path) or os.path.lexists(dest)):
            state = 'absent'

        # if it already exists and the source file isn't there, consider this done
        elif not os.path.lexists(path) and os.path.lexists(dest):
            state = 'compress'

        else:
            if module.check_mode:
                if not os.path.exists(dest):
                    changed = True
            else:
                size = 0
                f_in = f_out = arcfile = None

                if os.path.lexists(dest):
                    size = os.path.getsize(dest)

                try:
                    if format == 'zip':
                        arcfile = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)
                        arcfile.write(path, path[len(arcroot):])
                        arcfile.close()
                        state = 'archive' # because all zip files are archives

                    else:
                        f_in = open(path, 'rb')

                        if format == 'gz':
                            f_out = gzip.open(dest, 'wb')
                        elif format == 'bz2':
                            f_out = bz2.BZ2File(dest, 'wb')
                        else:
                            raise OSError("Invalid format")

                        shutil.copyfileobj(f_in, f_out)

                    successes.append(path)

                except OSError as e:
                    module.fail_json(path=path, dest=dest, msg='Unable to write to compressed file: %s' % to_native(e), exception=format_exc())

                if arcfile:
                    arcfile.close()
                if f_in:
                    f_in.close()
                if f_out:
                    f_out.close()

                # Rudimentary check: If size changed then file changed. Not perfect, but easy.
                if os.path.getsize(dest) != size:
                    changed = True

            state = 'compress'

        if remove and not check_mode:
            try:
                os.remove(path)

            except OSError as e:
                module.fail_json(path=path, msg='Unable to remove source file: %s' % to_native(e), exception=format_exc())

    params['path'] = dest
    file_args = module.load_file_common_arguments(params)

    if not check_mode:
        changed = module.set_fs_attributes_if_different(file_args, changed)

    module.exit_json(archived=successes,
                     dest=dest,
                     changed=changed,
                     state=state,
                     arcroot=arcroot,
                     missing=missing,
                     expanded_paths=expanded_paths,
                     expanded_exclude_paths=expanded_exclude_paths)

if __name__ == '__main__':
    main()

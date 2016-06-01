#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
(c) 2016, Ben Doherty <bendohmv@gmail.com>
Sponsored by Oomph, Inc. http://www.oomphinc.com

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: archive
version_added: 2.2
short_description: Creates a compressed archive of one or more files or trees.
extends_documentation_fragment: files
description:
     - The M(archive) module packs an archive. It is the opposite of the unarchive module. By default, it assumes the compression source exists on the target. It will not copy the source file from the local system to the target before archiving. Source files can be deleted after archival by specifying C(remove)=I(True).
options:
  path:
    description:
      - Remote absolute path, glob, or list of paths or globs for the file or files to compress or archive.
    required: true
  compression:
    description:
      - The type of compression to use. Can be 'gz', 'bz2', or 'zip'.
    choices: [ 'gz', 'bz2', 'zip' ]
    default: 'gz'
  dest:
    description:
      - The file name of the destination archive. This is required when C(path) refers to multiple files by either specifying a glob, a directory or multiple paths in a list.
    required: false
    default: null
  remove:
    description:
      - Remove any added source files and trees after adding to archive.
    type: bool
    required: false
    default: false

author: "Ben Doherty (@bendoh)"
notes:
    - requires tarfile, zipfile, gzip, and bzip2 packages on target host
    - can produce I(gzip), I(bzip2) and I(zip) compressed files or archives
'''

EXAMPLES = '''
# Compress directory /path/to/foo/ into /path/to/foo.tgz
- archive: path=/path/to/foo dest=/path/to/foo.tgz

# Compress regular file /path/to/foo into /path/to/foo.gz and remove it
- archive: path=/path/to/foo remove=True

# Create a zip archive of /path/to/foo
- archive: path=/path/to/foo compression=zip

# Create a bz2 archive of multiple files, rooted at /path
- archive:
    path:
        - /path/to/foo
        - /path/wong/foo
    dest: /path/file.tar.bz2
    compression: bz2
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
expanded_paths:
    description: The list of matching paths from paths argument.
    type: list
'''

import stat
import os
import errno
import glob
import shutil
import gzip
import bz2
import filecmp
import zipfile
import tarfile

def main():
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(type='list', required=True),
            compression = dict(choices=['gz', 'bz2', 'zip'], default='gz', required=False),
            dest = dict(required=False),
            remove = dict(required=False, default=False, type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    paths = params['path']
    dest = params['dest']
    remove = params['remove']
    expanded_paths = []
    compression = params['compression']
    globby = False
    changed = False
    state = 'absent'

    # Simple or archive file compression (inapplicable with 'zip' since it's always an archive)
    archive = False
    successes = []

    for i, path in enumerate(paths):
        path = os.path.expanduser(path)

        # Detect glob-like characters
        if any((c in set('*?')) for c in path):
            expanded_paths = expanded_paths + glob.glob(path)
        else:
            expanded_paths.append(path)

    if len(expanded_paths) == 0:
        return module.fail_json(path=', '.join(paths), expanded_paths=', '.join(expanded_paths), msg='Error, no source paths were found')

    # If we actually matched multiple files or TRIED to, then
    # treat this as a multi-file archive
    archive = globby or os.path.isdir(expanded_paths[0]) or len(expanded_paths) > 1

    # Default created file name (for single-file archives) to
    # <file>.<compression>
    if not archive and not dest:
        dest = '%s.%s' % (expanded_paths[0], compression)

    # Force archives to specify 'dest'
    if archive and not dest:
        module.fail_json(dest=dest, path=', '.join(paths), msg='Error, must specify "dest" when archiving multiple files or trees')

    archive_paths = []
    missing = []
    exclude = []
    arcroot = ''

    for path in expanded_paths:
        # Use the longest common directory name among all the files
        # as the archive root path
        if arcroot == '':
            arcroot = os.path.dirname(path) + os.sep
        else:
            for i in xrange(len(arcroot)):
                if path[i] != arcroot[i]:
                    break

            if i < len(arcroot):
                arcroot = os.path.dirname(arcroot[0:i+1])

            arcroot += os.sep

        # Don't allow archives to be created anywhere within paths to be removed
        if remove and os.path.isdir(path) and dest.startswith(path):
            module.fail_json(path=', '.join(paths), msg='Error, created archive can not be contained in source paths when remove=True')

        if os.path.lexists(path):
            archive_paths.append(path)
        else:
            missing.append(path)

    # No source files were found but the named archive exists: are we 'compress' or 'archive' now?
    if len(missing) == len(expanded_paths) and dest and os.path.exists(dest):
        # Just check the filename to know if it's an archive or simple compressed file
        if re.search(r'(\.tar\.gz|\.tgz|.tbz2|\.tar\.bz2|\.zip)$', os.path.basename(dest), re.IGNORECASE):
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
            try:

                # Slightly more difficult (and less efficient!) compression using zipfile module
                if compression == 'zip':
                    arcfile = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)

                # Easier compression using tarfile module
                elif compression == 'gz' or compression == 'bz2':
                    arcfile = tarfile.open(dest, 'w|' + compression)

                for path in archive_paths:
                    basename = ''

                    # Prefix trees in the archive with their basename, unless specifically prevented with '.'
                    if os.path.isdir(path) and not path.endswith(os.sep + '.'):
                        basename = os.path.basename(path) + os.sep

                    for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                        for dirname in dirnames:
                            fullpath = dirpath + os.sep + dirname

                            try:
                                if compression == 'zip':
                                    arcfile.write(fullpath, basename + dirname)
                                else:
                                    arcfile.add(fullpath, basename + dirname, recursive=False)

                            except Exception:
                                e = get_exception()
                                errors.append('%s: %s' % (fullpath, str(e)))

                        for filename in filenames:
                            fullpath = dirpath + os.sep + filename

                            if not filecmp.cmp(fullpath, dest):
                                try:
                                    if compression == 'zip':
                                        arcfile.write(fullpath, basename + filename)
                                    else:
                                        arcfile.add(fullpath, basename + filename, recursive=False)

                                    successes.append(fullpath)
                                except Exception:
                                    e = get_exception()
                                    errors.append('Adding %s: %s' % (path, str(e)))

            except Exception:
                e = get_exception()
                return module.fail_json(msg='Error when writing %s archive at %s: %s' % (compression == 'zip' and 'zip' or ('tar.' + compression), dest, str(e)))

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
                    else:
                        os.remove(path)
                except OSError:
                    e = get_exception()
                    errors.append(path)

            if len(errors) > 0:
                module.fail_json(dest=dest, msg='Error deleting some source files: ' + str(e), files=errors)

        # Rudimentary check: If size changed then file changed. Not perfect, but easy.
        if os.path.getsize(dest) != size:
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
                f_in = f_out = archive = None

                if os.path.lexists(dest):
                    size = os.path.getsize(dest)

                try:
                    if compression == 'zip':
                        archive = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)
                        archive.write(path, path[len(arcroot):])
                        archive.close()
                        state = 'archive' # because all zip files are archives

                    else:
                        f_in = open(path, 'rb')

                        if compression == 'gz':
                            f_out = gzip.open(dest, 'wb')
                        elif compression == 'bz2':
                            f_out = bz2.BZ2File(dest, 'wb')
                        else:
                            raise OSError("Invalid compression")

                        shutil.copyfileobj(f_in, f_out)

                    successes.append(path)

                except OSError:
                    e = get_exception()

                    module.fail_json(path=path, dest=dest, msg='Unable to write to compressed file: %s' % str(e))

                if archive:
                    archive.close()
                if f_in:
                    f_in.close()
                if f_out:
                    f_out.close()

                # Rudimentary check: If size changed then file changed. Not perfect, but easy.
                if os.path.getsize(dest) != size:
                    changed = True

            state = 'compress'

        if remove:
            try:
                os.remove(path)

            except OSError:
                e = get_exception()
                module.fail_json(path=path, msg='Unable to remove source file: %s' % str(e))

    module.exit_json(archived=successes, dest=dest, changed=changed, state=state, arcroot=arcroot, missing=missing, expanded_paths=expanded_paths)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()

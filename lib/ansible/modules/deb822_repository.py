# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
author: 'Ansible Core Team (@ansible)'
short_description: 'Add and remove deb822 formatted repositories'
description:
- 'Add and remove deb822 formatted repositories in Debian based distributions'
module: deb822_repository
notes:
- This module will not automatically update caches, call the apt module based
  on the changed state.
options:
    allow_downgrade_to_insecure:
        description:
        - Allow downgrading a package that was previously authenticated but
          is no longer authenticated
        type: bool
    allow_insecure:
        description:
        - Allow insecure repositories
        type: bool
    allow_weak:
        description:
        - Allow repositories signed with a key using a weak digest algorithm
        type: bool
    architectures:
        description:
        - 'Architectures to search within repository'
        type: list
        elements: str
    by_hash:
        description:
        - Controls if APT should try to acquire indexes via a URI constructed
          from a hashsum of the expected file instead of using the well-known
          stable filename of the index.
        type: bool
    check_date:
        description:
        - Controls if APT should consider the machine's time correct and hence
          perform time related checks, such as verifying that a Release file
          is not from the future.
        type: bool
    check_valid_until:
        description:
        - Controls if APT should try to detect replay attacks.
        type: bool
    components:
        description:
        - Components specify different sections of one distribution version
          present in a Suite.
        type: list
        elements: str
    date_max_future:
        description:
        - Controls how far from the future a repository may be.
        type: int
    enabled:
        description:
        - Tells APT whether the source is enabled or not.
        type: bool
    inrelease_path:
        description:
        - Determines the path to the InRelease file, relative to the normal
          position of an InRelease file.
        type: str
    languages:
        description:
        - Defines which languages information such as translated
          package descriptions should be downloaded.
        type: list
        elements: str
    name:
        description:
        - Name of the repo. Specifically used for C(X-Repolib-Name) and in
          naming the repository and signing key files.
        required: true
        type: str
    pdiffs:
        description:
        - Controls if APT should try to use PDiffs to update old indexes
          instead of downloading the new indexes entirely
        type: bool
    signed_by:
        description:
        - Either a URL to a GPG key, absolute path to a keyring file, one or
          more fingerprints of keys either in the C(trusted.gpg) keyring or in
          the keyrings in the C(trusted.gpg.d/) directory, or an ASCII armored
          GPG public key block.
        type: str
    suites:
        description:
        - >-
          Suite can specify an exact path in relation to the URI(s) provided,
          in which case the Components: must be omitted and suite must end
          with a slash C( / ). Alternatively, it may take the form of a
          distribution version (e.g. a version codename like disco or artful).
          If the suite does not specify a path, at least one component must
          be present.
        type: list
        elements: str
    targets:
        description:
        - Defines which download targets apt will try to acquire from this
          source.
        type: list
        elements: str
    trusted:
        description:
        - Decides if a source is considered trusted or if warnings should be
          raised before e.g. packages are installed from this source.
        type: bool
    types:
        choices:
        - deb
        - deb-src
        default:
        - deb
        type: list
        elements: str
        description:
        - Which types of packages to look for from a given source; either
          binary C(deb) or source code C(deb-src)
    uris:
        description:
        - The URIs must specify the base of the Debian distribution archive,
          from which APT finds the information it needs.
        type: list
        elements: str
    mode:
        description:
        - The octal mode for newly created files in sources.list.d.
        type: raw
        default: '0644'
    state:
        description:
        - A source string state.
        type: str
        choices:
        - absent
        - present
        default: present
requirements:
    - python3-debian / python-debian
version_added: '2.15'
'''

EXAMPLES = '''
- name: Add debian repo
  deb822_repository:
    name: debian
    types: deb
    uris: http://deb.debian.org/debian
    suites: stretch
    components:
      - main
      - contrib
      - non-free

- name: Add debian repo with key
  deb822_repository:
    name: debian
    types: deb
    uris: https://deb.debian.org
    suites: stable
    components:
      - main
      - contrib
      - non-free
    signed_by: |-
      -----BEGIN PGP PUBLIC KEY BLOCK-----

      mDMEYCQjIxYJKwYBBAHaRw8BAQdAD/P5Nvvnvk66SxBBHDbhRml9ORg1WV5CvzKY
      CuMfoIS0BmFiY2RlZoiQBBMWCgA4FiEErCIG1VhKWMWo2yfAREZd5NfO31cFAmAk
      IyMCGyMFCwkIBwMFFQoJCAsFFgIDAQACHgECF4AACgkQREZd5NfO31fbOwD6ArzS
      dM0Dkd5h2Ujy1b6KcAaVW9FOa5UNfJ9FFBtjLQEBAJ7UyWD3dZzhvlaAwunsk7DG
      3bHcln8DMpIJVXht78sL
      =IE0r
      -----END PGP PUBLIC KEY BLOCK-----

- name: Add repo using key from URL
  deb822_repository:
    name: example
    types: deb
    uris: https://download.example.com/linux/ubuntu
    suites: '{{ ansible_distribution_release }}'
    components: stable
    architectures: amd64
    signed_by: https://download.example.com/linux/ubuntu/gpg
'''

RETURN = '''
repo:
  description: A source string for the repository
  returned: always
  type: str
  sample: |
    X-Repolib-Name: debian
    Types: deb
    URIs: https://deb.debian.org
    Suites: stable
    Components: main contrib non-free
    Signed-By:
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        .
        mDMEYCQjIxYJKwYBBAHaRw8BAQdAD/P5Nvvnvk66SxBBHDbhRml9ORg1WV5CvzKY
        CuMfoIS0BmFiY2RlZoiQBBMWCgA4FiEErCIG1VhKWMWo2yfAREZd5NfO31cFAmAk
        IyMCGyMFCwkIBwMFFQoJCAsFFgIDAQACHgECF4AACgkQREZd5NfO31fbOwD6ArzS
        dM0Dkd5h2Ujy1b6KcAaVW9FOa5UNfJ9FFBtjLQEBAJ7UyWD3dZzhvlaAwunsk7DG
        3bHcln8DMpIJVXht78sL
        =IE0r
        -----END PGP PUBLIC KEY BLOCK-----

dest:
  description: Path to the repository file
  returned: always
  type: str
  sample: /etc/apt/sources.list.d/focal-archive.sources

key_filename:
  description: Path to the signed_by key file
  returned: always
  type: str
  sample: /etc/apt/keyrings/debian.gpg
'''

import os
import re
import tempfile
import textwrap
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.six import raise_from  # type: ignore[attr-defined]
from ansible.module_utils.urls import generic_urlparse
from ansible.module_utils.urls import open_url
from ansible.module_utils.urls import urlparse

HAS_DEBIAN = True
DEBIAN_IMP_ERR = None
try:
    from debian.deb822 import Deb822  # type: ignore[import]
except ImportError:
    HAS_DEBIAN = False
    DEBIAN_IMP_ERR = traceback.format_exc()

KEYRINGS_DIR = '/etc/apt/keyrings'


def ensure_keyrings_dir(module):
    changed = False
    if not os.path.isdir(KEYRINGS_DIR):
        if not module.check_mode:
            os.mkdir(KEYRINGS_DIR, 0o755)
        changed |= True

    changed |= module.set_fs_attributes_if_different(
        {
            'path': KEYRINGS_DIR,
            'secontext': [None, None, None],
            'owner': 'root',
            'group': 'root',
            'mode': '0755',
            'attributes': None,
        },
        changed,
    )

    return changed


def make_signed_by_filename(slug, ext):
    return os.path.join(KEYRINGS_DIR, '%s.%s' % (slug, ext))


def make_sources_filename(slug):
    return os.path.join(
        '/etc/apt/sources.list.d',
        '%s.sources' % slug
    )


def format_bool(v):
    return 'yes' if v else 'no'


def format_list(v):
    return ' '.join(v)


def format_multiline(v):
    return '\n' + textwrap.indent(
        '\n'.join(line.strip() or '.' for line in v.strip().splitlines()),
        '    '
    )


def format_field_name(v):
    if v == 'name':
        return 'X-Repolib-Name'
    elif v == 'uris':
        return 'URIs'
    return v.replace('_', '-').title()


def is_armored(b_data):
    return b'-----BEGIN PGP PUBLIC KEY BLOCK-----' in b_data


def write_signed_by_key(module, v, slug):
    changed = False
    if os.path.isfile(v):
        return changed, v, None

    b_data = None

    parts = generic_urlparse(urlparse(v))
    if parts.scheme:
        try:
            r = open_url(v, http_agent='ansible-httpget')
        except Exception as exc:
            raise_from(RuntimeError(to_native(exc)), exc)
        else:
            b_data = r.read()
    else:
        # Not a file, nor a URL, just pass it through
        return changed, None, v

    if not b_data:
        return changed, v, None

    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.write(b_data)

    ext = 'asc' if is_armored(b_data) else 'gpg'
    filename = make_signed_by_filename(slug, ext)

    src_chksum = module.sha256(tmpfile)
    dest_chksum = module.sha256(filename)

    if src_chksum != dest_chksum:
        changed |= ensure_keyrings_dir(module)
        if not module.check_mode:
            module.atomic_move(tmpfile, filename)
        changed |= True

    changed |= module.set_mode_if_different(filename, 0o0644, False)

    return changed, filename, None


def main():
    module = AnsibleModule(
        argument_spec={
            'allow_downgrade_to_insecure': {
                'type': 'bool',
            },
            'allow_insecure': {
                'type': 'bool',
            },
            'allow_weak': {
                'type': 'bool',
            },
            'architectures': {
                'elements': 'str',
                'type': 'list',
            },
            'by_hash': {
                'type': 'bool',
            },
            'check_date': {
                'type': 'bool',
            },
            'check_valid_until': {
                'type': 'bool',
            },
            'components': {
                'elements': 'str',
                'type': 'list',
            },
            'date_max_future': {
                'type': 'int',
            },
            'enabled': {
                'type': 'bool',
            },
            'inrelease_path': {
                'type': 'str',
            },
            'languages': {
                'elements': 'str',
                'type': 'list',
            },
            'name': {
                'type': 'str',
                'required': True,
            },
            'pdiffs': {
                'type': 'bool',
            },
            'signed_by': {
                'type': 'str',
            },
            'suites': {
                'elements': 'str',
                'type': 'list',
            },
            'targets': {
                'elements': 'str',
                'type': 'list',
            },
            'trusted': {
                'type': 'bool',
            },
            'types': {
                'choices': [
                    'deb',
                    'deb-src',
                ],
                'elements': 'str',
                'type': 'list',
                'default': [
                    'deb',
                ]
            },
            'uris': {
                'elements': 'str',
                'type': 'list',
            },
            # non-deb822 args
            'mode': {
                'type': 'raw',
                'default': '0644',
            },
            'state': {
                'type': 'str',
                'choices': [
                    'present',
                    'absent',
                ],
                'default': 'present',
            },
        },
        supports_check_mode=True,
    )

    if not HAS_DEBIAN:
        module.fail_json(msg=missing_required_lib("python3-debian"),
                         exception=DEBIAN_IMP_ERR)

    check_mode = module.check_mode

    changed = False

    # Make a copy, so we don't mutate module.params to avoid future issues
    params = module.params.copy()

    # popped non-deb822 args
    mode = params.pop('mode')
    state = params.pop('state')

    name = params['name']
    slug = re.sub(
        r'[^a-z0-9-]+',
        '',
        re.sub(
            r'[_\s]+',
            '-',
            name.lower(),
        ),
    )
    sources_filename = make_sources_filename(slug)

    if state == 'absent':
        if os.path.exists(sources_filename):
            if not check_mode:
                os.unlink(sources_filename)
            changed |= True
        for ext in ('asc', 'gpg'):
            signed_by_filename = make_signed_by_filename(slug, ext)
            if os.path.exists(signed_by_filename):
                if not check_mode:
                    os.unlink(signed_by_filename)
                changed = True
        module.exit_json(
            repo=None,
            changed=changed,
            dest=sources_filename,
            key_filename=signed_by_filename,
        )

    deb822 = Deb822()
    signed_by_filename = None
    for key, value in params.items():
        if value is None:
            continue

        if isinstance(value, bool):
            value = format_bool(value)
        elif isinstance(value, int):
            value = to_native(value)
        elif is_sequence(value):
            value = format_list(value)
        elif key == 'signed_by':
            try:
                key_changed, signed_by_filename, signed_by_data = write_signed_by_key(module, value, slug)
                value = signed_by_filename or signed_by_data
                changed |= key_changed
            except RuntimeError as exc:
                module.fail_json(
                    msg='Could not fetch signed_by key: %s' % to_native(exc)
                )

        if value.count('\n') > 0:
            value = format_multiline(value)

        deb822[format_field_name(key)] = value

    repo = deb822.dump()
    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.write(to_bytes(repo))

    sources_filename = make_sources_filename(slug)

    src_chksum = module.sha256(tmpfile)
    dest_chksum = module.sha256(sources_filename)

    if src_chksum != dest_chksum:
        if not check_mode:
            module.atomic_move(tmpfile, sources_filename)
        changed |= True

    changed |= module.set_mode_if_different(sources_filename, mode, False)

    module.exit_json(
        repo=repo,
        changed=changed,
        dest=sources_filename,
        key_filename=signed_by_filename,
    )


if __name__ == '__main__':
    main()

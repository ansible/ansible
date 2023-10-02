#!/usr/bin/env python
# Copyright: (c) 2013, James Cammarata <jcammarata@ansible.com>
# Copyright: (c) 2018-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI

import functools
import json
import os.path
import re
import shutil
import sys
import textwrap
import time
import typing as t

from dataclasses import dataclass
from yaml.error import YAMLError

import ansible.constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import Galaxy, get_collections_galaxy_meta_info
from ansible.galaxy.api import GalaxyAPI, GalaxyError
from ansible.galaxy.collection import (
    build_collection,
    download_collections,
    find_existing_collections,
    install_collections,
    publish_collection,
    validate_collection_name,
    validate_collection_path,
    verify_collections,
    SIGNATURE_COUNT_RE,
)
from ansible.galaxy.collection.concrete_artifact_manager import (
    ConcreteArtifactsManager,
)
from ansible.galaxy.collection.gpg import GPG_ERROR_MAP
from ansible.galaxy.dependency_resolution.dataclasses import Requirement

from ansible.galaxy.role import GalaxyRole
from ansible.galaxy.token import BasicAuthToken, GalaxyToken, KeycloakToken, NoTokenSentinel
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.common.yaml import yaml_dump, yaml_load
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils import six
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.playbook.role.requirement import RoleRequirement
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink

display = Display()
urlparse = six.moves.urllib.parse.urlparse

# config definition by position: name, required, type
SERVER_DEF = [
    ('url', True, 'str'),
    ('username', False, 'str'),
    ('password', False, 'str'),
    ('token', False, 'str'),
    ('auth_url', False, 'str'),
    ('v3', False, 'bool'),
    ('validate_certs', False, 'bool'),
    ('client_id', False, 'str'),
    ('timeout', False, 'int'),
]

# config definition fields
SERVER_ADDITIONAL = {
    'v3': {'default': 'False'},
    'validate_certs': {'cli': [{'name': 'validate_certs'}]},
    'timeout': {'default': '60', 'cli': [{'name': 'timeout'}]},
    'token': {'default': None},
}


def with_collection_artifacts_manager(wrapped_method):
    """Inject an artifacts manager if not passed explicitly.

    This decorator constructs a ConcreteArtifactsManager and maintains
    the related temporary directory auto-cleanup around the target
    method invocation.
    """
    @functools.wraps(wrapped_method)
    def method_wrapper(*args, **kwargs):
        if 'artifacts_manager' in kwargs:
            return wrapped_method(*args, **kwargs)

        # FIXME: use validate_certs context from Galaxy servers when downloading collections
        artifacts_manager_kwargs = {'validate_certs': context.CLIARGS['resolved_validate_certs']}

        keyring = context.CLIARGS.get('keyring', None)
        if keyring is not None:
            artifacts_manager_kwargs.update({
                'keyring': GalaxyCLI._resolve_path(keyring),
                'required_signature_count': context.CLIARGS.get('required_valid_signature_count', None),
                'ignore_signature_errors': context.CLIARGS.get('ignore_gpg_errors', None),
            })

        with ConcreteArtifactsManager.under_tmpdir(
                C.DEFAULT_LOCAL_TMP,
                **artifacts_manager_kwargs
        ) as concrete_artifact_cm:
            kwargs['artifacts_manager'] = concrete_artifact_cm
            return wrapped_method(*args, **kwargs)
    return method_wrapper


def _display_header(path, h1, h2, w1=10, w2=7):
    display.display('\n# {0}\n{1:{cwidth}} {2:{vwidth}}\n{3} {4}\n'.format(
        path,
        h1,
        h2,
        '-' * max([len(h1), w1]),  # Make sure that the number of dashes is at least the width of the header
        '-' * max([len(h2), w2]),
        cwidth=w1,
        vwidth=w2,
    ))


def _display_role(gr):
    install_info = gr.install_info
    version = None
    if install_info:
        version = install_info.get("version", None)
    if not version:
        version = "(unknown version)"
    display.display("- %s, %s" % (gr.name, version))


def _display_collection(collection, cwidth=10, vwidth=7, min_cwidth=10, min_vwidth=7):
    display.display('{fqcn:{cwidth}} {version:{vwidth}}'.format(
        fqcn=to_text(collection.fqcn),
        version=collection.ver,
        cwidth=max(cwidth, min_cwidth),  # Make sure the width isn't smaller than the header
        vwidth=max(vwidth, min_vwidth)
    ))


def _get_collection_widths(collections):
    if not is_iterable(collections):
        collections = (collections, )

    fqcn_set = {to_text(c.fqcn) for c in collections}
    version_set = {to_text(c.ver) for c in collections}

    fqcn_length = len(max(fqcn_set, key=len))
    version_length = len(max(version_set, key=len))

    return fqcn_length, version_length


def validate_signature_count(value):
    match = re.match(SIGNATURE_COUNT_RE, value)

    if match is None:
        raise ValueError(f"{value} is not a valid signature count value")

    return value


@dataclass
class RoleDistributionServer:
    _api: t.Union[GalaxyAPI, None]
    api_servers: list[GalaxyAPI]

    @property
    def api(self):
        if self._api:
            return self._api

        for server in self.api_servers:
            try:
                if u'v1' in server.available_api_versions:
                    self._api = server
                    break
            except Exception:
                continue

        if not self._api:
            self._api = self.api_servers[0]

        return self._api


class GalaxyCLI(CLI):
    '''Command to manage Ansible roles and collections.

       None of the CLI tools are designed to run concurrently with themselves.
       Use an external scheduler and/or locking to ensure there are no clashing operations.
    '''

    name = 'ansible-galaxy'

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")

    def __init__(self, args):
        self._raw_args = args
        self._implicit_role = False

        if len(args) > 1:
            # Inject role into sys.argv[1] as a backwards compatibility step
            if args[1] not in ['-h', '--help', '--version'] and 'role' not in args and 'collection' not in args:
                # TODO: Should we add a warning here and eventually deprecate the implicit role subcommand choice
                args.insert(1, 'role')
                self._implicit_role = True
            # since argparse doesn't allow hidden subparsers, handle dead login arg from raw args after "role" normalization
            if args[1:3] == ['role', 'login']:
                display.error(
                    "The login command was removed in late 2020. An API key is now required to publish roles or collections "
                    "to Galaxy. The key can be found at https://galaxy.ansible.com/me/preferences, and passed to the "
                    "ansible-galaxy CLI via a file at {0} or (insecurely) via the `--token` "
                    "command-line argument.".format(to_text(C.GALAXY_TOKEN_PATH)))
                sys.exit(1)

        self.api_servers = []
        self.galaxy = None
        self.lazy_role_api = None
        super(GalaxyCLI, self).__init__(args)

    def init_parser(self):
        ''' create an options parser for bin/ansible '''

        super(GalaxyCLI, self).init_parser(
            desc="Perform various Role and Collection related operations.",
        )

        # Common arguments that apply to more than 1 action
        common = opt_help.argparse.ArgumentParser(add_help=False)
        common.add_argument('-s', '--server', dest='api_server', help='The Galaxy API server URL')
        common.add_argument('--token', '--api-key', dest='api_key',
                            help='The Ansible Galaxy API key which can be found at '
                                 'https://galaxy.ansible.com/me/preferences.')
        common.add_argument('-c', '--ignore-certs', action='store_true', dest='ignore_certs', help='Ignore SSL certificate validation errors.', default=None)
        common.add_argument('--timeout', dest='timeout', type=int, default=60,
                            help="The time to wait for operations against the galaxy server, defaults to 60s.")

        opt_help.add_verbosity_options(common)

        force = opt_help.argparse.ArgumentParser(add_help=False)
        force.add_argument('-f', '--force', dest='force', action='store_true', default=False,
                           help='Force overwriting an existing role or collection')

        github = opt_help.argparse.ArgumentParser(add_help=False)
        github.add_argument('github_user', help='GitHub username')
        github.add_argument('github_repo', help='GitHub repository')

        offline = opt_help.argparse.ArgumentParser(add_help=False)
        offline.add_argument('--offline', dest='offline', default=False, action='store_true',
                             help="Don't query the galaxy API when creating roles")

        default_roles_path = C.config.get_configuration_definition('DEFAULT_ROLES_PATH').get('default', '')
        roles_path = opt_help.argparse.ArgumentParser(add_help=False)
        roles_path.add_argument('-p', '--roles-path', dest='roles_path', type=opt_help.unfrack_path(pathsep=True),
                                default=C.DEFAULT_ROLES_PATH, action=opt_help.PrependListAction,
                                help='The path to the directory containing your roles. The default is the first '
                                     'writable one configured via DEFAULT_ROLES_PATH: %s ' % default_roles_path)

        collections_path = opt_help.argparse.ArgumentParser(add_help=False)
        collections_path.add_argument('-p', '--collections-path', dest='collections_path', type=opt_help.unfrack_path(pathsep=True),
                                      default=AnsibleCollectionConfig.collection_paths,
                                      action=opt_help.PrependListAction,
                                      help="One or more directories to search for collections in addition "
                                      "to the default COLLECTIONS_PATHS. Separate multiple paths "
                                      "with '{0}'.".format(os.path.pathsep))

        cache_options = opt_help.argparse.ArgumentParser(add_help=False)
        cache_options.add_argument('--clear-response-cache', dest='clear_response_cache', action='store_true',
                                   default=False, help='Clear the existing server response cache.')
        cache_options.add_argument('--no-cache', dest='no_cache', action='store_true', default=False,
                                   help='Do not use the server response cache.')

        # Add sub parser for the Galaxy role type (role or collection)
        type_parser = self.parser.add_subparsers(metavar='TYPE', dest='type')
        type_parser.required = True

        # Add sub parser for the Galaxy collection actions
        collection = type_parser.add_parser('collection', help='Manage an Ansible Galaxy collection.')
        collection.set_defaults(func=self.execute_collection)  # to satisfy doc build
        collection_parser = collection.add_subparsers(metavar='COLLECTION_ACTION', dest='action')
        collection_parser.required = True
        self.add_download_options(collection_parser, parents=[common, cache_options])
        self.add_init_options(collection_parser, parents=[common, force])
        self.add_build_options(collection_parser, parents=[common, force])
        self.add_publish_options(collection_parser, parents=[common])
        self.add_install_options(collection_parser, parents=[common, force, cache_options])
        self.add_list_options(collection_parser, parents=[common, collections_path])
        self.add_verify_options(collection_parser, parents=[common, collections_path])

        # Add sub parser for the Galaxy role actions
        role = type_parser.add_parser('role', help='Manage an Ansible Galaxy role.')
        role.set_defaults(func=self.execute_role)  # to satisfy doc build
        role_parser = role.add_subparsers(metavar='ROLE_ACTION', dest='action')
        role_parser.required = True
        self.add_init_options(role_parser, parents=[common, force, offline])
        self.add_remove_options(role_parser, parents=[common, roles_path])
        self.add_delete_options(role_parser, parents=[common, github])
        self.add_list_options(role_parser, parents=[common, roles_path])
        self.add_search_options(role_parser, parents=[common])
        self.add_import_options(role_parser, parents=[common, github])
        self.add_setup_options(role_parser, parents=[common, roles_path])

        self.add_info_options(role_parser, parents=[common, roles_path, offline])
        self.add_install_options(role_parser, parents=[common, force, roles_path])

    def add_download_options(self, parser, parents=None):
        download_parser = parser.add_parser('download', parents=parents,
                                            help='Download collections and their dependencies as a tarball for an '
                                                 'offline install.')
        download_parser.set_defaults(func=self.execute_download)

        download_parser.add_argument('args', help='Collection(s)', metavar='collection', nargs='*')

        download_parser.add_argument('-n', '--no-deps', dest='no_deps', action='store_true', default=False,
                                     help="Don't download collection(s) listed as dependencies.")

        download_parser.add_argument('-p', '--download-path', dest='download_path',
                                     default='./collections',
                                     help='The directory to download the collections to.')
        download_parser.add_argument('-r', '--requirements-file', dest='requirements',
                                     help='A file containing a list of collections to be downloaded.')
        download_parser.add_argument('--pre', dest='allow_pre_release', action='store_true',
                                     help='Include pre-release versions. Semantic versioning pre-releases are ignored by default')

    def add_init_options(self, parser, parents=None):
        galaxy_type = 'collection' if parser.metavar == 'COLLECTION_ACTION' else 'role'

        init_parser = parser.add_parser('init', parents=parents,
                                        help='Initialize new {0} with the base structure of a '
                                             '{0}.'.format(galaxy_type))
        init_parser.set_defaults(func=self.execute_init)

        init_parser.add_argument('--init-path', dest='init_path', default='./',
                                 help='The path in which the skeleton {0} will be created. The default is the '
                                      'current working directory.'.format(galaxy_type))
        init_parser.add_argument('--{0}-skeleton'.format(galaxy_type), dest='{0}_skeleton'.format(galaxy_type),
                                 default=C.GALAXY_COLLECTION_SKELETON if galaxy_type == 'collection' else C.GALAXY_ROLE_SKELETON,
                                 help='The path to a {0} skeleton that the new {0} should be based '
                                      'upon.'.format(galaxy_type))

        obj_name_kwargs = {}
        if galaxy_type == 'collection':
            obj_name_kwargs['type'] = validate_collection_name
        init_parser.add_argument('{0}_name'.format(galaxy_type), help='{0} name'.format(galaxy_type.capitalize()),
                                 **obj_name_kwargs)

        if galaxy_type == 'role':
            init_parser.add_argument('--type', dest='role_type', action='store', default='default',
                                     help="Initialize using an alternate role type. Valid types include: 'container', "
                                          "'apb' and 'network'.")

    def add_remove_options(self, parser, parents=None):
        remove_parser = parser.add_parser('remove', parents=parents, help='Delete roles from roles_path.')
        remove_parser.set_defaults(func=self.execute_remove)

        remove_parser.add_argument('args', help='Role(s)', metavar='role', nargs='+')

    def add_delete_options(self, parser, parents=None):
        delete_parser = parser.add_parser('delete', parents=parents,
                                          help='Removes the role from Galaxy. It does not remove or alter the actual '
                                               'GitHub repository.')
        delete_parser.set_defaults(func=self.execute_delete)

    def add_list_options(self, parser, parents=None):
        galaxy_type = 'role'
        if parser.metavar == 'COLLECTION_ACTION':
            galaxy_type = 'collection'

        list_parser = parser.add_parser('list', parents=parents,
                                        help='Show the name and version of each {0} installed in the {0}s_path.'.format(galaxy_type))

        list_parser.set_defaults(func=self.execute_list)

        list_parser.add_argument(galaxy_type, help=galaxy_type.capitalize(), nargs='?', metavar=galaxy_type)

        if galaxy_type == 'collection':
            list_parser.add_argument('--format', dest='output_format', choices=('human', 'yaml', 'json'), default='human',
                                     help="Format to display the list of collections in.")

    def add_search_options(self, parser, parents=None):
        search_parser = parser.add_parser('search', parents=parents,
                                          help='Search the Galaxy database by tags, platforms, author and multiple '
                                               'keywords.')
        search_parser.set_defaults(func=self.execute_search)

        search_parser.add_argument('--platforms', dest='platforms', help='list of OS platforms to filter by')
        search_parser.add_argument('--galaxy-tags', dest='galaxy_tags', help='list of galaxy tags to filter by')
        search_parser.add_argument('--author', dest='author', help='GitHub username')
        search_parser.add_argument('args', help='Search terms', metavar='searchterm', nargs='*')

    def add_import_options(self, parser, parents=None):
        import_parser = parser.add_parser('import', parents=parents, help='Import a role into a galaxy server')
        import_parser.set_defaults(func=self.execute_import)

        import_parser.add_argument('--no-wait', dest='wait', action='store_false', default=True,
                                   help="Don't wait for import results.")
        import_parser.add_argument('--branch', dest='reference',
                                   help='The name of a branch to import. Defaults to the repository\'s default branch '
                                        '(usually master)')
        import_parser.add_argument('--role-name', dest='role_name',
                                   help='The name the role should have, if different than the repo name')
        import_parser.add_argument('--status', dest='check_status', action='store_true', default=False,
                                   help='Check the status of the most recent import request for given github_'
                                        'user/github_repo.')

    def add_setup_options(self, parser, parents=None):
        setup_parser = parser.add_parser('setup', parents=parents,
                                         help='Manage the integration between Galaxy and the given source.')
        setup_parser.set_defaults(func=self.execute_setup)

        setup_parser.add_argument('--remove', dest='remove_id', default=None,
                                  help='Remove the integration matching the provided ID value. Use --list to see '
                                       'ID values.')
        setup_parser.add_argument('--list', dest="setup_list", action='store_true', default=False,
                                  help='List all of your integrations.')
        setup_parser.add_argument('source', help='Source')
        setup_parser.add_argument('github_user', help='GitHub username')
        setup_parser.add_argument('github_repo', help='GitHub repository')
        setup_parser.add_argument('secret', help='Secret')

    def add_info_options(self, parser, parents=None):
        info_parser = parser.add_parser('info', parents=parents, help='View more details about a specific role.')
        info_parser.set_defaults(func=self.execute_info)

        info_parser.add_argument('args', nargs='+', help='role', metavar='role_name[,version]')

    def add_verify_options(self, parser, parents=None):
        galaxy_type = 'collection'
        verify_parser = parser.add_parser('verify', parents=parents, help='Compare checksums with the collection(s) '
                                          'found on the server and the installed copy. This does not verify dependencies.')
        verify_parser.set_defaults(func=self.execute_verify)

        verify_parser.add_argument('args', metavar='{0}_name'.format(galaxy_type), nargs='*', help='The installed collection(s) name. '
                                   'This is mutually exclusive with --requirements-file.')
        verify_parser.add_argument('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                   help='Ignore errors during verification and continue with the next specified collection.')
        verify_parser.add_argument('--offline', dest='offline', action='store_true', default=False,
                                   help='Validate collection integrity locally without contacting server for '
                                        'canonical manifest hash.')
        verify_parser.add_argument('-r', '--requirements-file', dest='requirements',
                                   help='A file containing a list of collections to be verified.')
        verify_parser.add_argument('--keyring', dest='keyring', default=C.GALAXY_GPG_KEYRING,
                                   help='The keyring used during signature verification')  # Eventually default to ~/.ansible/pubring.kbx?
        verify_parser.add_argument('--signature', dest='signatures', action='append',
                                   help='An additional signature source to verify the authenticity of the MANIFEST.json before using '
                                        'it to verify the rest of the contents of a collection from a Galaxy server. Use in '
                                        'conjunction with a positional collection name (mutually exclusive with --requirements-file).')
        valid_signature_count_help = 'The number of signatures that must successfully verify the collection. This should be a positive integer ' \
                                     'or all to signify that all signatures must be used to verify the collection. ' \
                                     'Prepend the value with + to fail if no valid signatures are found for the collection (e.g. +all).'
        ignore_gpg_status_help = 'A status code to ignore during signature verification (for example, NO_PUBKEY). ' \
                                 'Provide this option multiple times to ignore a list of status codes. ' \
                                 'Descriptions for the choices can be seen at L(https://github.com/gpg/gnupg/blob/master/doc/DETAILS#general-status-codes).'
        verify_parser.add_argument('--required-valid-signature-count', dest='required_valid_signature_count', type=validate_signature_count,
                                   help=valid_signature_count_help, default=C.GALAXY_REQUIRED_VALID_SIGNATURE_COUNT)
        verify_parser.add_argument('--ignore-signature-status-code', dest='ignore_gpg_errors', type=str, action='append',
                                   help=ignore_gpg_status_help, default=C.GALAXY_IGNORE_INVALID_SIGNATURE_STATUS_CODES,
                                   choices=list(GPG_ERROR_MAP.keys()))

    def add_install_options(self, parser, parents=None):
        galaxy_type = 'collection' if parser.metavar == 'COLLECTION_ACTION' else 'role'

        args_kwargs = {}
        if galaxy_type == 'collection':
            args_kwargs['help'] = 'The collection(s) name or path/url to a tar.gz collection artifact. This is ' \
                                  'mutually exclusive with --requirements-file.'
            ignore_errors_help = 'Ignore errors during installation and continue with the next specified ' \
                                 'collection. This will not ignore dependency conflict errors.'
        else:
            args_kwargs['help'] = 'Role name, URL or tar file'
            ignore_errors_help = 'Ignore errors and continue with the next specified role.'

        install_parser = parser.add_parser('install', parents=parents,
                                           help='Install {0}(s) from file(s), URL(s) or Ansible '
                                                'Galaxy'.format(galaxy_type))
        install_parser.set_defaults(func=self.execute_install)

        install_parser.add_argument('args', metavar='{0}_name'.format(galaxy_type), nargs='*', **args_kwargs)
        install_parser.add_argument('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                    help=ignore_errors_help)

        install_exclusive = install_parser.add_mutually_exclusive_group()
        install_exclusive.add_argument('-n', '--no-deps', dest='no_deps', action='store_true', default=False,
                                       help="Don't download {0}s listed as dependencies.".format(galaxy_type))
        install_exclusive.add_argument('--force-with-deps', dest='force_with_deps', action='store_true', default=False,
                                       help="Force overwriting an existing {0} and its "
                                            "dependencies.".format(galaxy_type))

        valid_signature_count_help = 'The number of signatures that must successfully verify the collection. This should be a positive integer ' \
                                     'or -1 to signify that all signatures must be used to verify the collection. ' \
                                     'Prepend the value with + to fail if no valid signatures are found for the collection (e.g. +all).'
        ignore_gpg_status_help = 'A status code to ignore during signature verification (for example, NO_PUBKEY). ' \
                                 'Provide this option multiple times to ignore a list of status codes. ' \
                                 'Descriptions for the choices can be seen at L(https://github.com/gpg/gnupg/blob/master/doc/DETAILS#general-status-codes).'

        if galaxy_type == 'collection':
            install_parser.add_argument('-p', '--collections-path', dest='collections_path',
                                        default=self._get_default_collection_path(),
                                        help='The path to the directory containing your collections.')
            install_parser.add_argument('-r', '--requirements-file', dest='requirements',
                                        help='A file containing a list of collections to be installed.')
            install_parser.add_argument('--pre', dest='allow_pre_release', action='store_true',
                                        help='Include pre-release versions. Semantic versioning pre-releases are ignored by default')
            install_parser.add_argument('-U', '--upgrade', dest='upgrade', action='store_true', default=False,
                                        help='Upgrade installed collection artifacts. This will also update dependencies unless --no-deps is provided')
            install_parser.add_argument('--keyring', dest='keyring', default=C.GALAXY_GPG_KEYRING,
                                        help='The keyring used during signature verification')  # Eventually default to ~/.ansible/pubring.kbx?
            install_parser.add_argument('--disable-gpg-verify', dest='disable_gpg_verify', action='store_true',
                                        default=C.GALAXY_DISABLE_GPG_VERIFY,
                                        help='Disable GPG signature verification when installing collections from a Galaxy server')
            install_parser.add_argument('--signature', dest='signatures', action='append',
                                        help='An additional signature source to verify the authenticity of the MANIFEST.json before '
                                             'installing the collection from a Galaxy server. Use in conjunction with a positional '
                                             'collection name (mutually exclusive with --requirements-file).')
            install_parser.add_argument('--required-valid-signature-count', dest='required_valid_signature_count', type=validate_signature_count,
                                        help=valid_signature_count_help, default=C.GALAXY_REQUIRED_VALID_SIGNATURE_COUNT)
            install_parser.add_argument('--ignore-signature-status-code', dest='ignore_gpg_errors', type=str, action='append',
                                        help=ignore_gpg_status_help, default=C.GALAXY_IGNORE_INVALID_SIGNATURE_STATUS_CODES,
                                        choices=list(GPG_ERROR_MAP.keys()))
            install_parser.add_argument('--offline', dest='offline', action='store_true', default=False,
                                        help='Install collection artifacts (tarballs) without contacting any distribution servers. '
                                             'This does not apply to collections in remote Git repositories or URLs to remote tarballs.'
                                        )
        else:
            install_parser.add_argument('-r', '--role-file', dest='requirements',
                                        help='A file containing a list of roles to be installed.')

            r_re = re.compile(r'^(?<!-)-[a-zA-Z]*r[a-zA-Z]*')  # -r, -fr
            contains_r = bool([a for a in self._raw_args if r_re.match(a)])
            role_file_re = re.compile(r'--role-file($|=)')  # --role-file foo, --role-file=foo
            contains_role_file = bool([a for a in self._raw_args if role_file_re.match(a)])
            if self._implicit_role and (contains_r or contains_role_file):
                # Any collections in the requirements files will also be installed
                install_parser.add_argument('--keyring', dest='keyring', default=C.GALAXY_GPG_KEYRING,
                                            help='The keyring used during collection signature verification')
                install_parser.add_argument('--disable-gpg-verify', dest='disable_gpg_verify', action='store_true',
                                            default=C.GALAXY_DISABLE_GPG_VERIFY,
                                            help='Disable GPG signature verification when installing collections from a Galaxy server')
                install_parser.add_argument('--required-valid-signature-count', dest='required_valid_signature_count', type=validate_signature_count,
                                            help=valid_signature_count_help, default=C.GALAXY_REQUIRED_VALID_SIGNATURE_COUNT)
                install_parser.add_argument('--ignore-signature-status-code', dest='ignore_gpg_errors', type=str, action='append',
                                            help=ignore_gpg_status_help, default=C.GALAXY_IGNORE_INVALID_SIGNATURE_STATUS_CODES,
                                            choices=list(GPG_ERROR_MAP.keys()))

            install_parser.add_argument('-g', '--keep-scm-meta', dest='keep_scm_meta', action='store_true',
                                        default=False,
                                        help='Use tar instead of the scm archive option when packaging the role.')

    def add_build_options(self, parser, parents=None):
        build_parser = parser.add_parser('build', parents=parents,
                                         help='Build an Ansible collection artifact that can be published to Ansible '
                                              'Galaxy.')
        build_parser.set_defaults(func=self.execute_build)

        build_parser.add_argument('args', metavar='collection', nargs='*', default=('.',),
                                  help='Path to the collection(s) directory to build. This should be the directory '
                                       'that contains the galaxy.yml file. The default is the current working '
                                       'directory.')
        build_parser.add_argument('--output-path', dest='output_path', default='./',
                                  help='The path in which the collection is built to. The default is the current '
                                       'working directory.')

    def add_publish_options(self, parser, parents=None):
        publish_parser = parser.add_parser('publish', parents=parents,
                                           help='Publish a collection artifact to Ansible Galaxy.')
        publish_parser.set_defaults(func=self.execute_publish)

        publish_parser.add_argument('args', metavar='collection_path',
                                    help='The path to the collection tarball to publish.')
        publish_parser.add_argument('--no-wait', dest='wait', action='store_false', default=True,
                                    help="Don't wait for import validation results.")
        publish_parser.add_argument('--import-timeout', dest='import_timeout', type=int, default=0,
                                    help="The time to wait for the collection import process to finish.")

    def post_process_args(self, options):
        options = super(GalaxyCLI, self).post_process_args(options)

        # ensure we have 'usable' cli option
        setattr(options, 'validate_certs', (None if options.ignore_certs is None else not options.ignore_certs))
        # the default if validate_certs is None
        setattr(options, 'resolved_validate_certs', (options.validate_certs if options.validate_certs is not None else not C.GALAXY_IGNORE_CERTS))

        display.verbosity = options.verbosity
        return options

    def run(self):

        super(GalaxyCLI, self).run()

        self.galaxy = Galaxy()

        def server_config_def(section, key, required, option_type):
            config_def = {
                'description': 'The %s of the %s Galaxy server' % (key, section),
                'ini': [
                    {
                        'section': 'galaxy_server.%s' % section,
                        'key': key,
                    }
                ],
                'env': [
                    {'name': 'ANSIBLE_GALAXY_SERVER_%s_%s' % (section.upper(), key.upper())},
                ],
                'required': required,
                'type': option_type,
            }
            if key in SERVER_ADDITIONAL:
                config_def.update(SERVER_ADDITIONAL[key])

            return config_def

        galaxy_options = {}
        for optional_key in ['clear_response_cache', 'no_cache', 'timeout']:
            if optional_key in context.CLIARGS:
                galaxy_options[optional_key] = context.CLIARGS[optional_key]

        config_servers = []

        # Need to filter out empty strings or non truthy values as an empty server list env var is equal to [''].
        server_list = [s for s in C.GALAXY_SERVER_LIST or [] if s]
        for server_priority, server_key in enumerate(server_list, start=1):
            # Abuse the 'plugin config' by making 'galaxy_server' a type of plugin
            # Config definitions are looked up dynamically based on the C.GALAXY_SERVER_LIST entry. We look up the
            # section [galaxy_server.<server>] for the values url, username, password, and token.
            config_dict = dict((k, server_config_def(server_key, k, req, ensure_type)) for k, req, ensure_type in SERVER_DEF)
            defs = AnsibleLoader(yaml_dump(config_dict)).get_single_data()
            C.config.initialize_plugin_configuration_definitions('galaxy_server', server_key, defs)

            # resolve the config created options above with existing config and user options
            server_options = C.config.get_plugin_options('galaxy_server', server_key)

            # auth_url is used to create the token, but not directly by GalaxyAPI, so
            # it doesn't need to be passed as kwarg to GalaxyApi, same for others we pop here
            auth_url = server_options.pop('auth_url')
            client_id = server_options.pop('client_id')
            token_val = server_options['token'] or NoTokenSentinel
            username = server_options['username']
            v3 = server_options.pop('v3')
            if server_options['validate_certs'] is None:
                server_options['validate_certs'] = context.CLIARGS['resolved_validate_certs']
            validate_certs = server_options['validate_certs']

            if v3:
                # This allows a user to explicitly indicate the server uses the /v3 API
                # This was added for testing against pulp_ansible and I'm not sure it has
                # a practical purpose outside of this use case. As such, this option is not
                # documented as of now
                server_options['available_api_versions'] = {'v3': '/v3'}

            # default case if no auth info is provided.
            server_options['token'] = None

            if username:
                server_options['token'] = BasicAuthToken(username, server_options['password'])
            else:
                if token_val:
                    if auth_url:
                        server_options['token'] = KeycloakToken(access_token=token_val,
                                                                auth_url=auth_url,
                                                                validate_certs=validate_certs,
                                                                client_id=client_id)
                    else:
                        # The galaxy v1 / github / django / 'Token'
                        server_options['token'] = GalaxyToken(token=token_val)

            server_options.update(galaxy_options)
            config_servers.append(GalaxyAPI(
                self.galaxy, server_key,
                priority=server_priority,
                **server_options
            ))

        cmd_server = context.CLIARGS['api_server']
        cmd_token = GalaxyToken(token=context.CLIARGS['api_key'])

        validate_certs = context.CLIARGS['resolved_validate_certs']
        if cmd_server:
            # Cmd args take precedence over the config entry but fist check if the arg was a name and use that config
            # entry, otherwise create a new API entry for the server specified.
            config_server = next((s for s in config_servers if s.name == cmd_server), None)
            if config_server:
                self.api_servers.append(config_server)
            else:
                self.api_servers.append(GalaxyAPI(
                    self.galaxy, 'cmd_arg', cmd_server, token=cmd_token,
                    priority=len(config_servers) + 1,
                    validate_certs=validate_certs,
                    **galaxy_options
                ))
        else:
            self.api_servers = config_servers

        # Default to C.GALAXY_SERVER if no servers were defined
        if len(self.api_servers) == 0:
            self.api_servers.append(GalaxyAPI(
                self.galaxy, 'default', C.GALAXY_SERVER, token=cmd_token,
                priority=0,
                validate_certs=validate_certs,
                **galaxy_options
            ))

        # checks api versions once a GalaxyRole makes an api call
        # self.api can be used to evaluate the best server immediately
        self.lazy_role_api = RoleDistributionServer(None, self.api_servers)

        return context.CLIARGS['func']()

    @property
    def api(self):
        return self.lazy_role_api.api

    def _get_default_collection_path(self):
        return C.COLLECTIONS_PATHS[0]

    def _parse_requirements_file(self, requirements_file, allow_old_format=True, artifacts_manager=None, validate_signature_options=True):
        """
        Parses an Ansible requirement.yml file and returns all the roles and/or collections defined in it. There are 2
        requirements file format:

            # v1 (roles only)
            - src: The source of the role, required if include is not set. Can be Galaxy role name, URL to a SCM repo or tarball.
              name: Downloads the role to the specified name, defaults to Galaxy name from Galaxy or name of repo if src is a URL.
              scm: If src is a URL, specify the SCM. Only git or hd are supported and defaults ot git.
              version: The version of the role to download. Can also be tag, commit, or branch name and defaults to master.
              include: Path to additional requirements.yml files.

            # v2 (roles and collections)
            ---
            roles:
            # Same as v1 format just under the roles key

            collections:
            - namespace.collection
            - name: namespace.collection
              version: version identifier, multiple identifiers are separated by ','
              source: the URL or a predefined source name that relates to C.GALAXY_SERVER_LIST
              type: git|file|url|galaxy

        :param requirements_file: The path to the requirements file.
        :param allow_old_format: Will fail if a v1 requirements file is found and this is set to False.
        :param artifacts_manager: Artifacts manager.
        :return: a dict containing roles and collections to found in the requirements file.
        """
        requirements = {
            'roles': [],
            'collections': [],
        }

        b_requirements_file = to_bytes(requirements_file, errors='surrogate_or_strict')
        if not os.path.exists(b_requirements_file):
            raise AnsibleError("The requirements file '%s' does not exist." % to_native(requirements_file))

        display.vvv("Reading requirement file at '%s'" % requirements_file)
        with open(b_requirements_file, 'rb') as req_obj:
            try:
                file_requirements = yaml_load(req_obj)
            except YAMLError as err:
                raise AnsibleError(
                    "Failed to parse the requirements yml at '%s' with the following error:\n%s"
                    % (to_native(requirements_file), to_native(err)))

        if file_requirements is None:
            raise AnsibleError("No requirements found in file '%s'" % to_native(requirements_file))

        def parse_role_req(requirement):
            if "include" not in requirement:
                role = RoleRequirement.role_yaml_parse(requirement)
                display.vvv("found role %s in yaml file" % to_text(role))
                if "name" not in role and "src" not in role:
                    raise AnsibleError("Must specify name or src for role")
                return [GalaxyRole(self.galaxy, self.lazy_role_api, **role)]
            else:
                b_include_path = to_bytes(requirement["include"], errors="surrogate_or_strict")
                if not os.path.isfile(b_include_path):
                    raise AnsibleError("Failed to find include requirements file '%s' in '%s'"
                                       % (to_native(b_include_path), to_native(requirements_file)))

                with open(b_include_path, 'rb') as f_include:
                    try:
                        return [GalaxyRole(self.galaxy, self.lazy_role_api, **r) for r in
                                (RoleRequirement.role_yaml_parse(i) for i in yaml_load(f_include))]
                    except Exception as e:
                        raise AnsibleError("Unable to load data from include requirements file: %s %s"
                                           % (to_native(requirements_file), to_native(e)))

        if isinstance(file_requirements, list):
            # Older format that contains only roles
            if not allow_old_format:
                raise AnsibleError("Expecting requirements file to be a dict with the key 'collections' that contains "
                                   "a list of collections to install")

            for role_req in file_requirements:
                requirements['roles'] += parse_role_req(role_req)

        else:
            # Newer format with a collections and/or roles key
            extra_keys = set(file_requirements.keys()).difference(set(['roles', 'collections']))
            if extra_keys:
                raise AnsibleError("Expecting only 'roles' and/or 'collections' as base keys in the requirements "
                                   "file. Found: %s" % (to_native(", ".join(extra_keys))))

            for role_req in file_requirements.get('roles') or []:
                requirements['roles'] += parse_role_req(role_req)

            requirements['collections'] = [
                Requirement.from_requirement_dict(
                    self._init_coll_req_dict(collection_req),
                    artifacts_manager,
                    validate_signature_options,
                )
                for collection_req in file_requirements.get('collections') or []
            ]

        return requirements

    def _init_coll_req_dict(self, coll_req):
        if not isinstance(coll_req, dict):
            # Assume it's a string:
            return {'name': coll_req}

        if (
                'name' not in coll_req or
                not coll_req.get('source') or
                coll_req.get('type', 'galaxy') != 'galaxy'
        ):
            return coll_req

        # Try and match up the requirement source with our list of Galaxy API
        # servers defined in the config, otherwise create a server with that
        # URL without any auth.
        coll_req['source'] = next(
            iter(
                srvr for srvr in self.api_servers
                if coll_req['source'] in {srvr.name, srvr.api_server}
            ),
            GalaxyAPI(
                self.galaxy,
                'explicit_requirement_{name!s}'.format(
                    name=coll_req['name'],
                ),
                coll_req['source'],
                validate_certs=context.CLIARGS['resolved_validate_certs'],
            ),
        )

        return coll_req

    @staticmethod
    def exit_without_ignore(rc=1):
        """
        Exits with the specified return code unless the
        option --ignore-errors was specified
        """
        if not context.CLIARGS['ignore_errors']:
            raise AnsibleError('- you can use --ignore-errors to skip failed roles and finish processing the list.')

    @staticmethod
    def _display_role_info(role_info):

        text = [u"", u"Role: %s" % to_text(role_info['name'])]

        # Get the top-level 'description' first, falling back to galaxy_info['galaxy_info']['description'].
        galaxy_info = role_info.get('galaxy_info', {})
        description = role_info.get('description', galaxy_info.get('description', ''))
        text.append(u"\tdescription: %s" % description)

        for k in sorted(role_info.keys()):

            if k in GalaxyCLI.SKIP_INFO_KEYS:
                continue

            if isinstance(role_info[k], dict):
                text.append(u"\t%s:" % (k))
                for key in sorted(role_info[k].keys()):
                    if key in GalaxyCLI.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
            else:
                text.append(u"\t%s: %s" % (k, role_info[k]))

        # make sure we have a trailing newline returned
        text.append(u"")
        return u'\n'.join(text)

    @staticmethod
    def _resolve_path(path):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))

    @staticmethod
    def _get_skeleton_galaxy_yml(template_path, inject_data):
        with open(to_bytes(template_path, errors='surrogate_or_strict'), 'rb') as template_obj:
            meta_template = to_text(template_obj.read(), errors='surrogate_or_strict')

        galaxy_meta = get_collections_galaxy_meta_info()

        required_config = []
        optional_config = []
        for meta_entry in galaxy_meta:
            config_list = required_config if meta_entry.get('required', False) else optional_config

            value = inject_data.get(meta_entry['key'], None)
            if not value:
                meta_type = meta_entry.get('type', 'str')

                if meta_type == 'str':
                    value = ''
                elif meta_type == 'list':
                    value = []
                elif meta_type == 'dict':
                    value = {}

            meta_entry['value'] = value
            config_list.append(meta_entry)

        link_pattern = re.compile(r"L\(([^)]+),\s+([^)]+)\)")
        const_pattern = re.compile(r"C\(([^)]+)\)")

        def comment_ify(v):
            if isinstance(v, list):
                v = ". ".join([l.rstrip('.') for l in v])

            v = link_pattern.sub(r"\1 <\2>", v)
            v = const_pattern.sub(r"'\1'", v)

            return textwrap.fill(v, width=117, initial_indent="# ", subsequent_indent="# ", break_on_hyphens=False)

        loader = DataLoader()
        templar = Templar(loader, variables={'required_config': required_config, 'optional_config': optional_config})
        templar.environment.filters['comment_ify'] = comment_ify

        meta_value = templar.template(meta_template)

        return meta_value

    def _require_one_of_collections_requirements(
            self, collections, requirements_file,
            signatures=None,
            artifacts_manager=None,
    ):
        if collections and requirements_file:
            raise AnsibleError("The positional collection_name arg and --requirements-file are mutually exclusive.")
        elif not collections and not requirements_file:
            raise AnsibleError("You must specify a collection name or a requirements file.")
        elif requirements_file:
            if signatures is not None:
                raise AnsibleError(
                    "The --signatures option and --requirements-file are mutually exclusive. "
                    "Use the --signatures with positional collection_name args or provide a "
                    "'signatures' key for requirements in the --requirements-file."
                )
            requirements_file = GalaxyCLI._resolve_path(requirements_file)
            requirements = self._parse_requirements_file(
                requirements_file,
                allow_old_format=False,
                artifacts_manager=artifacts_manager,
            )
        else:
            requirements = {
                'collections': [
                    Requirement.from_string(coll_input, artifacts_manager, signatures)
                    for coll_input in collections
                ],
                'roles': [],
            }
        return requirements

    ############################
    # execute actions
    ############################

    def execute_role(self):
        """
        Perform the action on an Ansible Galaxy role. Must be combined with a further action like delete/install/init
        as listed below.
        """
        # To satisfy doc build
        pass

    def execute_collection(self):
        """
        Perform the action on an Ansible Galaxy collection. Must be combined with a further action like init/install as
        listed below.
        """
        # To satisfy doc build
        pass

    def execute_build(self):
        """
        Build an Ansible Galaxy collection artifact that can be stored in a central repository like Ansible Galaxy.
        By default, this command builds from the current working directory. You can optionally pass in the
        collection input path (where the ``galaxy.yml`` file is).
        """
        force = context.CLIARGS['force']
        output_path = GalaxyCLI._resolve_path(context.CLIARGS['output_path'])
        b_output_path = to_bytes(output_path, errors='surrogate_or_strict')

        if not os.path.exists(b_output_path):
            os.makedirs(b_output_path)
        elif os.path.isfile(b_output_path):
            raise AnsibleError("- the output collection directory %s is a file - aborting" % to_native(output_path))

        for collection_path in context.CLIARGS['args']:
            collection_path = GalaxyCLI._resolve_path(collection_path)
            build_collection(
                to_text(collection_path, errors='surrogate_or_strict'),
                to_text(output_path, errors='surrogate_or_strict'),
                force,
            )

    @with_collection_artifacts_manager
    def execute_download(self, artifacts_manager=None):
        """Download collections and their dependencies as a tarball for an offline install."""
        collections = context.CLIARGS['args']
        no_deps = context.CLIARGS['no_deps']
        download_path = context.CLIARGS['download_path']

        requirements_file = context.CLIARGS['requirements']
        if requirements_file:
            requirements_file = GalaxyCLI._resolve_path(requirements_file)

        requirements = self._require_one_of_collections_requirements(
            collections, requirements_file,
            artifacts_manager=artifacts_manager,
        )['collections']

        download_path = GalaxyCLI._resolve_path(download_path)
        b_download_path = to_bytes(download_path, errors='surrogate_or_strict')
        if not os.path.exists(b_download_path):
            os.makedirs(b_download_path)

        download_collections(
            requirements, download_path, self.api_servers, no_deps,
            context.CLIARGS['allow_pre_release'],
            artifacts_manager=artifacts_manager,
        )

        return 0

    def execute_init(self):
        """
        Creates the skeleton framework of a role or collection that complies with the Galaxy metadata format.
        Requires a role or collection name. The collection name must be in the format ``<namespace>.<collection>``.
        """

        galaxy_type = context.CLIARGS['type']
        init_path = context.CLIARGS['init_path']
        force = context.CLIARGS['force']
        obj_skeleton = context.CLIARGS['{0}_skeleton'.format(galaxy_type)]

        obj_name = context.CLIARGS['{0}_name'.format(galaxy_type)]

        inject_data = dict(
            description='your {0} description'.format(galaxy_type),
            ansible_plugin_list_dir=get_versioned_doclink('plugins/plugins.html'),
        )
        if galaxy_type == 'role':
            inject_data.update(dict(
                author='your name',
                company='your company (optional)',
                license='license (GPL-2.0-or-later, MIT, etc)',
                role_name=obj_name,
                role_type=context.CLIARGS['role_type'],
                issue_tracker_url='http://example.com/issue/tracker',
                repository_url='http://example.com/repository',
                documentation_url='http://docs.example.com',
                homepage_url='http://example.com',
                min_ansible_version=ansible_version[:3],  # x.y
                dependencies=[],
            ))

            skeleton_ignore_expressions = C.GALAXY_ROLE_SKELETON_IGNORE
            obj_path = os.path.join(init_path, obj_name)
        elif galaxy_type == 'collection':
            namespace, collection_name = obj_name.split('.', 1)

            inject_data.update(dict(
                namespace=namespace,
                collection_name=collection_name,
                version='1.0.0',
                readme='README.md',
                authors=['your name <example@domain.com>'],
                license=['GPL-2.0-or-later'],
                repository='http://example.com/repository',
                documentation='http://docs.example.com',
                homepage='http://example.com',
                issues='http://example.com/issue/tracker',
                build_ignore=[],
            ))

            skeleton_ignore_expressions = C.GALAXY_COLLECTION_SKELETON_IGNORE
            obj_path = os.path.join(init_path, namespace, collection_name)

        b_obj_path = to_bytes(obj_path, errors='surrogate_or_strict')

        if os.path.exists(b_obj_path):
            if os.path.isfile(obj_path):
                raise AnsibleError("- the path %s already exists, but is a file - aborting" % to_native(obj_path))
            elif not force:
                raise AnsibleError("- the directory %s already exists. "
                                   "You can use --force to re-initialize this directory,\n"
                                   "however it will reset any main.yml files that may have\n"
                                   "been modified there already." % to_native(obj_path))

            # delete the contents rather than the collection root in case init was run from the root (--init-path ../../)
            for root, dirs, files in os.walk(b_obj_path, topdown=True):
                for old_dir in dirs:
                    path = os.path.join(root, old_dir)
                    shutil.rmtree(path)
                for old_file in files:
                    path = os.path.join(root, old_file)
                    os.unlink(path)

        if obj_skeleton is not None:
            own_skeleton = False
        else:
            own_skeleton = True
            obj_skeleton = self.galaxy.default_role_skeleton_path
            skeleton_ignore_expressions = ['^.*/.git_keep$']

        obj_skeleton = os.path.expanduser(obj_skeleton)
        skeleton_ignore_re = [re.compile(x) for x in skeleton_ignore_expressions]

        if not os.path.exists(obj_skeleton):
            raise AnsibleError("- the skeleton path '{0}' does not exist, cannot init {1}".format(
                to_native(obj_skeleton), galaxy_type)
            )

        loader = DataLoader()
        templar = Templar(loader, variables=inject_data)

        # create role directory
        if not os.path.exists(b_obj_path):
            os.makedirs(b_obj_path)

        for root, dirs, files in os.walk(obj_skeleton, topdown=True):
            rel_root = os.path.relpath(root, obj_skeleton)
            rel_dirs = rel_root.split(os.sep)
            rel_root_dir = rel_dirs[0]
            if galaxy_type == 'collection':
                # A collection can contain templates in playbooks/*/templates and roles/*/templates
                in_templates_dir = rel_root_dir in ['playbooks', 'roles'] and 'templates' in rel_dirs
            else:
                in_templates_dir = rel_root_dir == 'templates'

            # Filter out ignored directory names
            # Use [:] to mutate the list os.walk uses
            dirs[:] = [d for d in dirs if not any(r.match(d) for r in skeleton_ignore_re)]

            for f in files:
                filename, ext = os.path.splitext(f)

                if any(r.match(os.path.join(rel_root, f)) for r in skeleton_ignore_re):
                    continue

                if galaxy_type == 'collection' and own_skeleton and rel_root == '.' and f == 'galaxy.yml.j2':
                    # Special use case for galaxy.yml.j2 in our own default collection skeleton. We build the options
                    # dynamically which requires special options to be set.

                    # The templated data's keys must match the key name but the inject data contains collection_name
                    # instead of name. We just make a copy and change the key back to name for this file.
                    template_data = inject_data.copy()
                    template_data['name'] = template_data.pop('collection_name')

                    meta_value = GalaxyCLI._get_skeleton_galaxy_yml(os.path.join(root, rel_root, f), template_data)
                    b_dest_file = to_bytes(os.path.join(obj_path, rel_root, filename), errors='surrogate_or_strict')
                    with open(b_dest_file, 'wb') as galaxy_obj:
                        galaxy_obj.write(to_bytes(meta_value, errors='surrogate_or_strict'))
                elif ext == ".j2" and not in_templates_dir:
                    src_template = os.path.join(root, f)
                    dest_file = os.path.join(obj_path, rel_root, filename)
                    template_data = to_text(loader._get_file_contents(src_template)[0], errors='surrogate_or_strict')
                    b_rendered = to_bytes(templar.template(template_data), errors='surrogate_or_strict')
                    with open(dest_file, 'wb') as df:
                        df.write(b_rendered)
                else:
                    f_rel_path = os.path.relpath(os.path.join(root, f), obj_skeleton)
                    shutil.copyfile(os.path.join(root, f), os.path.join(obj_path, f_rel_path))

            for d in dirs:
                b_dir_path = to_bytes(os.path.join(obj_path, rel_root, d), errors='surrogate_or_strict')
                if not os.path.exists(b_dir_path):
                    os.makedirs(b_dir_path)

        display.display("- %s %s was created successfully" % (galaxy_type.title(), obj_name))

    def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        roles_path = context.CLIARGS['roles_path']

        data = ''
        for role in context.CLIARGS['args']:

            role_info = {'path': roles_path}
            gr = GalaxyRole(self.galaxy, self.lazy_role_api, role)

            install_info = gr.install_info
            if install_info:
                if 'version' in install_info:
                    install_info['installed_version'] = install_info['version']
                    del install_info['version']
                role_info.update(install_info)

            if not context.CLIARGS['offline']:
                remote_data = None
                try:
                    remote_data = self.api.lookup_role_by_name(role, False)
                except GalaxyError as e:
                    if e.http_code == 400 and 'Bad Request' in e.message:
                        # Role does not exist in Ansible Galaxy
                        data = u"- the role %s was not found" % role
                        break

                    raise AnsibleError("Unable to find info about '%s': %s" % (role, e))

                if remote_data:
                    role_info.update(remote_data)
                else:
                    data = u"- the role %s was not found" % role
                    break

            elif context.CLIARGS['offline'] and not gr._exists:
                data = u"- the role %s was not found" % role
                break

            if gr.metadata:
                role_info.update(gr.metadata)

            req = RoleRequirement()
            role_spec = req.role_yaml_parse({'role': role})
            if role_spec:
                role_info.update(role_spec)

            data += self._display_role_info(role_info)

        self.pager(data)

    @with_collection_artifacts_manager
    def execute_verify(self, artifacts_manager=None):
        """Compare checksums with the collection(s) found on the server and the installed copy. This does not verify dependencies."""

        collections = context.CLIARGS['args']
        search_paths = context.CLIARGS['collections_path']
        ignore_errors = context.CLIARGS['ignore_errors']
        local_verify_only = context.CLIARGS['offline']
        requirements_file = context.CLIARGS['requirements']
        signatures = context.CLIARGS['signatures']
        if signatures is not None:
            signatures = list(signatures)

        requirements = self._require_one_of_collections_requirements(
            collections, requirements_file,
            signatures=signatures,
            artifacts_manager=artifacts_manager,
        )['collections']

        resolved_paths = [validate_collection_path(GalaxyCLI._resolve_path(path)) for path in search_paths]

        results = verify_collections(
            requirements, resolved_paths,
            self.api_servers, ignore_errors,
            local_verify_only=local_verify_only,
            artifacts_manager=artifacts_manager,
        )

        if any(result for result in results if not result.success):
            return 1

        return 0

    @with_collection_artifacts_manager
    def execute_install(self, artifacts_manager=None):
        """
        Install one or more roles(``ansible-galaxy role install``), or one or more collections(``ansible-galaxy collection install``).
        You can pass in a list (roles or collections) or use the file
        option listed below (these are mutually exclusive). If you pass in a list, it
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local tar archive file.
        """
        install_items = context.CLIARGS['args']
        requirements_file = context.CLIARGS['requirements']
        collection_path = None
        signatures = context.CLIARGS.get('signatures')
        if signatures is not None:
            signatures = list(signatures)

        if requirements_file:
            requirements_file = GalaxyCLI._resolve_path(requirements_file)

        two_type_warning = "The requirements file '%s' contains {0}s which will be ignored. To install these {0}s " \
                           "run 'ansible-galaxy {0} install -r' or to install both at the same time run " \
                           "'ansible-galaxy install -r' without a custom install path." % to_text(requirements_file)

        # TODO: Would be nice to share the same behaviour with args and -r in collections and roles.
        collection_requirements = []
        role_requirements = []
        if context.CLIARGS['type'] == 'collection':
            collection_path = GalaxyCLI._resolve_path(context.CLIARGS['collections_path'])
            requirements = self._require_one_of_collections_requirements(
                install_items, requirements_file,
                signatures=signatures,
                artifacts_manager=artifacts_manager,
            )

            collection_requirements = requirements['collections']
            if requirements['roles']:
                display.vvv(two_type_warning.format('role'))
        else:
            if not install_items and requirements_file is None:
                raise AnsibleOptionsError("- you must specify a user/role name or a roles file")

            if requirements_file:
                if not (requirements_file.endswith('.yaml') or requirements_file.endswith('.yml')):
                    raise AnsibleError("Invalid role requirements file, it must end with a .yml or .yaml extension")

                galaxy_args = self._raw_args
                will_install_collections = self._implicit_role and '-p' not in galaxy_args and '--roles-path' not in galaxy_args

                requirements = self._parse_requirements_file(
                    requirements_file,
                    artifacts_manager=artifacts_manager,
                    validate_signature_options=will_install_collections,
                )
                role_requirements = requirements['roles']

                # We can only install collections and roles at the same time if the type wasn't specified and the -p
                # argument was not used. If collections are present in the requirements then at least display a msg.
                if requirements['collections'] and (not self._implicit_role or '-p' in galaxy_args or
                                                    '--roles-path' in galaxy_args):

                    # We only want to display a warning if 'ansible-galaxy install -r ... -p ...'. Other cases the user
                    # was explicit about the type and shouldn't care that collections were skipped.
                    display_func = display.warning if self._implicit_role else display.vvv
                    display_func(two_type_warning.format('collection'))
                else:
                    collection_path = self._get_default_collection_path()
                    collection_requirements = requirements['collections']
            else:
                # roles were specified directly, so we'll just go out grab them
                # (and their dependencies, unless the user doesn't want us to).
                for rname in context.CLIARGS['args']:
                    role = RoleRequirement.role_yaml_parse(rname.strip())
                    role_requirements.append(GalaxyRole(self.galaxy, self.lazy_role_api, **role))

        if not role_requirements and not collection_requirements:
            display.display("Skipping install, no requirements found")
            return

        if role_requirements:
            display.display("Starting galaxy role install process")
            self._execute_install_role(role_requirements)

        if collection_requirements:
            display.display("Starting galaxy collection install process")
            # Collections can technically be installed even when ansible-galaxy is in role mode so we need to pass in
            # the install path as context.CLIARGS['collections_path'] won't be set (default is calculated above).
            self._execute_install_collection(
                collection_requirements, collection_path,
                artifacts_manager=artifacts_manager,
            )

    def _execute_install_collection(
            self, requirements, path, artifacts_manager,
    ):
        force = context.CLIARGS['force']
        ignore_errors = context.CLIARGS['ignore_errors']
        no_deps = context.CLIARGS['no_deps']
        force_with_deps = context.CLIARGS['force_with_deps']
        try:
            disable_gpg_verify = context.CLIARGS['disable_gpg_verify']
        except KeyError:
            if self._implicit_role:
                raise AnsibleError(
                    'Unable to properly parse command line arguments. Please use "ansible-galaxy collection install" '
                    'instead of "ansible-galaxy install".'
                )
            raise

        # If `ansible-galaxy install` is used, collection-only options aren't available to the user and won't be in context.CLIARGS
        allow_pre_release = context.CLIARGS.get('allow_pre_release', False)
        upgrade = context.CLIARGS.get('upgrade', False)

        collections_path = C.COLLECTIONS_PATHS
        if len([p for p in collections_path if p.startswith(path)]) == 0:
            display.warning("The specified collections path '%s' is not part of the configured Ansible "
                            "collections paths '%s'. The installed collection will not be picked up in an Ansible "
                            "run, unless within a playbook-adjacent collections directory." % (to_text(path), to_text(":".join(collections_path))))

        output_path = validate_collection_path(path)
        b_output_path = to_bytes(output_path, errors='surrogate_or_strict')
        if not os.path.exists(b_output_path):
            os.makedirs(b_output_path)

        install_collections(
            requirements, output_path, self.api_servers, ignore_errors,
            no_deps, force, force_with_deps, upgrade,
            allow_pre_release=allow_pre_release,
            artifacts_manager=artifacts_manager,
            disable_gpg_verify=disable_gpg_verify,
            offline=context.CLIARGS.get('offline', False),
        )

        return 0

    def _execute_install_role(self, requirements):
        role_file = context.CLIARGS['requirements']
        no_deps = context.CLIARGS['no_deps']
        force_deps = context.CLIARGS['force_with_deps']
        force = context.CLIARGS['force'] or force_deps

        for role in requirements:
            # only process roles in roles files when names matches if given
            if role_file and context.CLIARGS['args'] and role.name not in context.CLIARGS['args']:
                display.vvv('Skipping role %s' % role.name)
                continue

            display.vvv('Processing role %s ' % role.name)

            # query the galaxy API for the role data

            if role.install_info is not None:
                if role.install_info['version'] != role.version or force:
                    if force:
                        display.display('- changing role %s from %s to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        role.remove()
                    else:
                        display.warning('- %s (%s) is already installed - use --force to change version to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        continue
                else:
                    if not force:
                        display.display('- %s is already installed, skipping.' % str(role))
                        continue

            try:
                installed = role.install()
            except AnsibleError as e:
                display.warning(u"- %s was NOT installed successfully: %s " % (role.name, to_text(e)))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            if not no_deps and installed:
                if not role.metadata:
                    # NOTE: the meta file is also required for installing the role, not just dependencies
                    display.warning("Meta file %s is empty. Skipping dependencies." % role.path)
                else:
                    role_dependencies = role.metadata_dependencies + role.requirements
                    for dep in role_dependencies:
                        display.debug('Installing dep %s' % dep)
                        dep_req = RoleRequirement()
                        dep_info = dep_req.role_yaml_parse(dep)
                        dep_role = GalaxyRole(self.galaxy, self.lazy_role_api, **dep_info)
                        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                            # we know we can skip this, as it's not going to
                            # be found on galaxy.ansible.com
                            continue
                        if dep_role.install_info is None:
                            if dep_role not in requirements:
                                display.display('- adding dependency: %s' % to_text(dep_role))
                                requirements.append(dep_role)
                            else:
                                display.display('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                if force_deps:
                                    display.display('- changing dependent role %s from %s to %s' %
                                                    (dep_role.name, dep_role.install_info['version'], dep_role.version or "unspecified"))
                                    dep_role.remove()
                                    requirements.append(dep_role)
                                else:
                                    display.warning('- dependency %s (%s) from role %s differs from already installed version (%s), skipping' %
                                                    (to_text(dep_role), dep_role.version, role.name, dep_role.install_info['version']))
                            else:
                                if force_deps:
                                    requirements.append(dep_role)
                                else:
                                    display.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                display.warning("- %s was NOT installed successfully." % role.name)
                self.exit_without_ignore()

        return 0

    def execute_remove(self):
        """
        removes the list of roles passed as arguments from the local system.
        """

        if not context.CLIARGS['args']:
            raise AnsibleOptionsError('- you must specify at least one role to remove.')

        for role_name in context.CLIARGS['args']:
            role = GalaxyRole(self.galaxy, self.api, role_name)
            try:
                if role.remove():
                    display.display('- successfully removed %s' % role_name)
                else:
                    display.display('- %s is not installed, skipping.' % role_name)
            except Exception as e:
                raise AnsibleError("Failed to remove role %s: %s" % (role_name, to_native(e)))

        return 0

    def execute_list(self):
        """
        List installed collections or roles
        """

        if context.CLIARGS['type'] == 'role':
            self.execute_list_role()
        elif context.CLIARGS['type'] == 'collection':
            self.execute_list_collection()

    def execute_list_role(self):
        """
        List all roles installed on the local system or a specific role
        """

        path_found = False
        role_found = False
        warnings = []
        roles_search_paths = context.CLIARGS['roles_path']
        role_name = context.CLIARGS['role']

        for path in roles_search_paths:
            role_path = GalaxyCLI._resolve_path(path)
            if os.path.isdir(path):
                path_found = True
            else:
                warnings.append("- the configured path {0} does not exist.".format(path))
                continue

            if role_name:
                # show the requested role, if it exists
                gr = GalaxyRole(self.galaxy, self.lazy_role_api, role_name, path=os.path.join(role_path, role_name))
                if os.path.isdir(gr.path):
                    role_found = True
                    display.display('# %s' % os.path.dirname(gr.path))
                    _display_role(gr)
                    break
                warnings.append("- the role %s was not found" % role_name)
            else:
                if not os.path.exists(role_path):
                    warnings.append("- the configured path %s does not exist." % role_path)
                    continue

                if not os.path.isdir(role_path):
                    warnings.append("- the configured path %s, exists, but it is not a directory." % role_path)
                    continue

                display.display('# %s' % role_path)
                path_files = os.listdir(role_path)
                for path_file in path_files:
                    gr = GalaxyRole(self.galaxy, self.lazy_role_api, path_file, path=path)
                    if gr.metadata:
                        _display_role(gr)

        # Do not warn if the role was found in any of the search paths
        if role_found and role_name:
            warnings = []

        for w in warnings:
            display.warning(w)

        if not path_found:
            raise AnsibleOptionsError("- None of the provided paths were usable. Please specify a valid path with --{0}s-path".format(context.CLIARGS['type']))

        return 0

    @with_collection_artifacts_manager
    def execute_list_collection(self, artifacts_manager=None):
        """
        List all collections installed on the local system

        :param artifacts_manager: Artifacts manager.
        """
        if artifacts_manager is not None:
            artifacts_manager.require_build_metadata = False

        output_format = context.CLIARGS['output_format']
        collections_search_paths = set(context.CLIARGS['collections_path'])
        collection_name = context.CLIARGS['collection']
        default_collections_path = AnsibleCollectionConfig.collection_paths
        collections_in_paths = {}

        warnings = []
        path_found = False
        collection_found = False
        for path in collections_search_paths:
            collection_path = GalaxyCLI._resolve_path(path)
            if not os.path.exists(path):
                if path in default_collections_path:
                    # don't warn for missing default paths
                    continue
                warnings.append("- the configured path {0} does not exist.".format(collection_path))
                continue

            if not os.path.isdir(collection_path):
                warnings.append("- the configured path {0}, exists, but it is not a directory.".format(collection_path))
                continue

            path_found = True

            if collection_name:
                # list a specific collection

                validate_collection_name(collection_name)
                namespace, collection = collection_name.split('.')

                collection_path = validate_collection_path(collection_path)
                b_collection_path = to_bytes(os.path.join(collection_path, namespace, collection), errors='surrogate_or_strict')

                if not os.path.exists(b_collection_path):
                    warnings.append("- unable to find {0} in collection paths".format(collection_name))
                    continue

                if not os.path.isdir(collection_path):
                    warnings.append("- the configured path {0}, exists, but it is not a directory.".format(collection_path))
                    continue

                collection_found = True

                try:
                    collection = Requirement.from_dir_path_as_unknown(
                        b_collection_path,
                        artifacts_manager,
                    )
                except ValueError as val_err:
                    six.raise_from(AnsibleError(val_err), val_err)

                if output_format in {'yaml', 'json'}:
                    collections_in_paths[collection_path] = {
                        collection.fqcn: {'version': collection.ver}
                    }

                    continue

                fqcn_width, version_width = _get_collection_widths([collection])

                _display_header(collection_path, 'Collection', 'Version', fqcn_width, version_width)
                _display_collection(collection, fqcn_width, version_width)

            else:
                # list all collections
                collection_path = validate_collection_path(path)
                if os.path.isdir(collection_path):
                    display.vvv("Searching {0} for collections".format(collection_path))
                    collections = list(find_existing_collections(
                        collection_path, artifacts_manager,
                    ))
                else:
                    # There was no 'ansible_collections/' directory in the path, so there
                    # or no collections here.
                    display.vvv("No 'ansible_collections' directory found at {0}".format(collection_path))
                    continue

                if not collections:
                    display.vvv("No collections found at {0}".format(collection_path))
                    continue

                if output_format in {'yaml', 'json'}:
                    collections_in_paths[collection_path] = {
                        collection.fqcn: {'version': collection.ver} for collection in collections
                    }

                    continue

                # Display header
                fqcn_width, version_width = _get_collection_widths(collections)
                _display_header(collection_path, 'Collection', 'Version', fqcn_width, version_width)

                # Sort collections by the namespace and name
                for collection in sorted(collections, key=to_text):
                    _display_collection(collection, fqcn_width, version_width)

        # Do not warn if the specific collection was found in any of the search paths
        if collection_found and collection_name:
            warnings = []

        for w in warnings:
            display.warning(w)

        if not path_found:
            raise AnsibleOptionsError("- None of the provided paths were usable. Please specify a valid path with --{0}s-path".format(context.CLIARGS['type']))

        if output_format == 'json':
            display.display(json.dumps(collections_in_paths))
        elif output_format == 'yaml':
            display.display(yaml_dump(collections_in_paths))

        return 0

    def execute_publish(self):
        """
        Publish a collection into Ansible Galaxy. Requires the path to the collection tarball to publish.
        """
        collection_path = GalaxyCLI._resolve_path(context.CLIARGS['args'])
        wait = context.CLIARGS['wait']
        timeout = context.CLIARGS['import_timeout']

        publish_collection(collection_path, self.api, wait, timeout)

    def execute_search(self):
        ''' searches for roles on the Ansible Galaxy server'''
        page_size = 1000
        search = None

        if context.CLIARGS['args']:
            search = '+'.join(context.CLIARGS['args'])

        if not search and not context.CLIARGS['platforms'] and not context.CLIARGS['galaxy_tags'] and not context.CLIARGS['author']:
            raise AnsibleError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=context.CLIARGS['platforms'],
                                         tags=context.CLIARGS['galaxy_tags'], author=context.CLIARGS['author'], page_size=page_size)

        if response['count'] == 0:
            display.display("No roles match your search.", color=C.COLOR_ERROR)
            return 1

        data = [u'']

        if response['count'] > page_size:
            data.append(u"Found %d roles matching your search. Showing first %s." % (response['count'], page_size))
        else:
            data.append(u"Found %d roles matching your search:" % response['count'])

        max_len = []
        for role in response['results']:
            max_len.append(len(role['username'] + '.' + role['name']))
        name_len = max(max_len)
        format_str = u" %%-%ds %%s" % name_len
        data.append(u'')
        data.append(format_str % (u"Name", u"Description"))
        data.append(format_str % (u"----", u"-----------"))
        for role in response['results']:
            data.append(format_str % (u'%s.%s' % (role['username'], role['name']), role['description']))

        data = u'\n'.join(data)
        self.pager(data)

        return 0

    def execute_import(self):
        """ used to import a role into Ansible Galaxy """

        colors = {
            'INFO': 'normal',
            'WARNING': C.COLOR_WARN,
            'ERROR': C.COLOR_ERROR,
            'SUCCESS': C.COLOR_OK,
            'FAILED': C.COLOR_ERROR,
        }

        github_user = to_text(context.CLIARGS['github_user'], errors='surrogate_or_strict')
        github_repo = to_text(context.CLIARGS['github_repo'], errors='surrogate_or_strict')

        if context.CLIARGS['check_status']:
            task = self.api.get_import_task(github_user=github_user, github_repo=github_repo)
        else:
            # Submit an import request
            task = self.api.create_import_task(github_user, github_repo,
                                               reference=context.CLIARGS['reference'],
                                               role_name=context.CLIARGS['role_name'])

            if len(task) > 1:
                # found multiple roles associated with github_user/github_repo
                display.display("WARNING: More than one Galaxy role associated with Github repo %s/%s." % (github_user, github_repo),
                                color='yellow')
                display.display("The following Galaxy roles are being updated:" + u'\n', color=C.COLOR_CHANGED)
                for t in task:
                    display.display('%s.%s' % (t['summary_fields']['role']['namespace'], t['summary_fields']['role']['name']), color=C.COLOR_CHANGED)
                display.display(u'\nTo properly namespace this role, remove each of the above and re-import %s/%s from scratch' % (github_user, github_repo),
                                color=C.COLOR_CHANGED)
                return 0
            # found a single role as expected
            display.display("Successfully submitted import request %d" % task[0]['id'])
            if not context.CLIARGS['wait']:
                display.display("Role name: %s" % task[0]['summary_fields']['role']['name'])
                display.display("Repo: %s/%s" % (task[0]['github_user'], task[0]['github_repo']))

        if context.CLIARGS['check_status'] or context.CLIARGS['wait']:
            # Get the status of the import
            msg_list = []
            finished = False
            while not finished:
                task = self.api.get_import_task(task_id=task[0]['id'])
                for msg in task[0]['summary_fields']['task_messages']:
                    if msg['id'] not in msg_list:
                        display.display(msg['message_text'], color=colors[msg['message_type']])
                        msg_list.append(msg['id'])
                if task[0]['state'] in ['SUCCESS', 'FAILED']:
                    finished = True
                else:
                    time.sleep(10)

        return 0

    def execute_setup(self):
        """ Setup an integration from Github or Travis for Ansible Galaxy roles"""

        if context.CLIARGS['setup_list']:
            # List existing integration secrets
            secrets = self.api.list_secrets()
            if len(secrets) == 0:
                # None found
                display.display("No integrations found.")
                return 0
            display.display(u'\n' + "ID         Source     Repo", color=C.COLOR_OK)
            display.display("---------- ---------- ----------", color=C.COLOR_OK)
            for secret in secrets:
                display.display("%-10s %-10s %s/%s" % (secret['id'], secret['source'], secret['github_user'],
                                                       secret['github_repo']), color=C.COLOR_OK)
            return 0

        if context.CLIARGS['remove_id']:
            # Remove a secret
            self.api.remove_secret(context.CLIARGS['remove_id'])
            display.display("Secret removed. Integrations using this secret will not longer work.", color=C.COLOR_OK)
            return 0

        source = context.CLIARGS['source']
        github_user = context.CLIARGS['github_user']
        github_repo = context.CLIARGS['github_repo']
        secret = context.CLIARGS['secret']

        resp = self.api.add_secret(source, github_user, github_repo, secret)
        display.display("Added integration for %s %s/%s" % (resp['source'], resp['github_user'], resp['github_repo']))

        return 0

    def execute_delete(self):
        """ Delete a role from Ansible Galaxy. """

        github_user = context.CLIARGS['github_user']
        github_repo = context.CLIARGS['github_repo']
        resp = self.api.delete_role(github_user, github_repo)

        if len(resp['deleted_roles']) > 1:
            display.display("Deleted the following roles:")
            display.display("ID     User            Name")
            display.display("------ --------------- ----------")
            for role in resp['deleted_roles']:
                display.display("%-8s %-15s %s" % (role.id, role.namespace, role.name))

        display.display(resp['status'])

        return 0


def main(args=None):
    GalaxyCLI.cli_executor(args)


if __name__ == '__main__':
    main()

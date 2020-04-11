from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
import re
import shutil
import textwrap
import time
import yaml

from jinja2 import BaseLoader, Environment, FileSystemLoader
from yaml.error import YAMLError

import ansible.constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import Galaxy, get_collections_galaxy_meta_info
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.collection import (
    build_collection,
    CollectionRequirement,
    download_collections,
    find_existing_collections,
    install_collections,
    publish_collection,
    validate_collection_name,
    validate_collection_path,
    verify_collections
)
from ansible.galaxy.login import GalaxyLogin
from ansible.galaxy.requirements import Requirements
from ansible.galaxy.role import GalaxyRole
from ansible.galaxy.token import BasicAuthToken, GalaxyToken, KeycloakToken, NoTokenSentinel
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils import six
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink

display = Display()

#TODO: Remove unnecessary files to import

class RolesAndCollections(Requirements):
    def __init__(self, file_reqs, req_file):
        extra_keys = set(file_reqs.keys()).difference(set(['roles', 'collections']))
        if extra_keys:
            raise AnsibleError("Expecting only 'roles' and/or 'collections' as base keys in the requirements file. Found: %s" % (to_native(", ".join(extra_keys))))
        super().__init__(file_reqs, req_file)

    def parse_reqs(self, galaxy_obj):
        for role_req in self.file_requirements.get('roles', []):
            self.requirements['roles'] += self.parse_role_req(galaxy_obj=galaxy_obj, requirement=role_req)

        for collection_req in self.file_requirements.get('collections', []):
            if isinstance(collection_req, dict):
                req_name = collection_req.get('name', None)
                if req_name is None:
                    raise AnsibleError("Collections requirement entry should contain the key name.")

                req_version = collection_req.get('version', '*')
                req_source = collection_req.get('source', None)
                if req_source:
                    # Try and match up the requirement source with our list of Galaxy API servers defined in the
                    # config, otherwise create a server with that URL without any auth.
                    req_source = next(iter([a for a in galaxy_obj.api_servers if req_source in [a.name, a.api_server]]), GalaxyAPI(galaxy_obj.galaxy, "explicit_requirement_%s" % req_name, req_source))

                self.requirements['collections'].append((req_name, req_version, req_source))
            else:
                self.requirements['collections'].append((collection_req, '*', None))

        return self.requirements
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

class Roles(Requirements):
    def __init__(self, file_reqs, req_file, allow_old_format):
        if not allow_old_format:
                raise AnsibleError("Expecting requirements file to be a dict with the key 'collections' that contains "
                                   "a list of collections to install")
        super().__init__(file_reqs, req_file)

    def parse_reqs(self, galaxy_obj):
        for role_req in self.file_requirements:
                self.requirements['roles'] += self.parse_role_req(galaxy_obj=galaxy_obj, requirement=role_req)
        return self.requirements
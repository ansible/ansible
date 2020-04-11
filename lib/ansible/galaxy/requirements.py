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

class Requirements():
    def __init__(self, file_reqs, req_file):
        self.file_requirements = file_reqs
        self.requirements_file = req_file
        self.requirements = {
            'roles': [],
            'collections': [],
        }

    
    def parse_role_req(self, galaxy_obj, requirement):
        if "include" not in requirement:
            role = RoleRequirement.role_yaml_parse(requirement)
            display.vvv("found role %s in yaml file" % to_text(role))
            if "name" not in role and "src" not in role:
                raise AnsibleError("Must specify name or src for role")
            return [GalaxyRole(galaxy_obj.galaxy, galaxy_obj.api, **role)]
        else:
            b_include_path = to_bytes(requirement["include"], errors="surrogate_or_strict")
            if not os.path.isfile(b_include_path):
                raise AnsibleError("Failed to find include requirements file '%s' in '%s'"
                                    % (to_native(b_include_path), to_native(self.requirements_file)))

            with open(b_include_path, 'rb') as f_include:
                try:
                    return [GalaxyRole(galaxy_obj.galaxy, galaxy_obj.api, **r) for r in
                            (RoleRequirement.role_yaml_parse(i) for i in yaml.safe_load(f_include))]
                except Exception as e:
                    raise AnsibleError("Unable to load data from include requirements file: %s %s"
                                        % (to_native(self.requirements_file), to_native(e)))

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

class RequirementsFile():

    def __init__(self, req_file, errors):
        self.file = req_file
        self.b_file = to_bytes(req_file, errors=errors)
        if not os.path.exists(self.file):
            raise AnsibleError("The requirements file '%s' does not exist." % to_native(req_file))
        self.file_requirements = None

    def open_file(self):
        with open(self.b_file, 'rb') as req_obj:
            try:
                self.file_requirements = yaml.safe_load(req_obj)
            except YAMLError as err:
                raise AnsibleError(
                    "Failed to parse the requirements yml at '%s' with the following error:\n%s"
                    % (to_native(self.file), to_native(err)))
            if self.file_requirements is None:
                raise AnsibleError("No requirements found in file '%s'" % to_native(self.file))

        return self.file_requirements
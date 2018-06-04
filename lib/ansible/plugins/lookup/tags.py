from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
      lookup: tags
        author: Nikita Chernyi <me+ansible@rakshazi.cf>
        version_added: "2.5"
        short_description: Get used tags
        description:
            - This lookup returns tags used when run ansible playbook
        options:
          _terms:
            description: tag to find. Returns boolean if set, returns list of tags if not set
            required: False
        notes:
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from __main__ import cli


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        tags = cli.options.tags
        if terms:
            for term in terms:
                return [term in tags]
        else:
            return tags

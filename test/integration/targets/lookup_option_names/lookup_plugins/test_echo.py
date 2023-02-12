# Taken from https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#lookup-plugins
# python 3 headers, required if submitting to Ansible
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
  name: test_echo
  author: Devon Mar (@devon-mar)
  version_added: "0.9"  # for collections, use the collection version, not the Ansible version
  short_description: Echo arguments.
  description:
      - This lookup returns a dict containing kwargs, terms and variables.
  options:
    _terms:
      description: path(s) of files to read
      required: True
    _kwargs:
      description:
            - Arbitrary kwargs
      type: dict
"""
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return [
            {
                "kwargs": kwargs,
                "terms": terms,
                "variables": variables,
            }
        ]

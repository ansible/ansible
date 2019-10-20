# (c) 2019, Ari Kalfus <dev@quantummadness.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
lookup: github_version
author:
  - Ari Kalfus (@Artis3n) <dev@quantummadness.com>
version_added: "2.8"
requirements:
  - json
  - re
  - urllib
short_description: Get the latest tagged release version from a public Github repository.
description:
  - This lookup returns the latest release tag of a public Github repository.
  - A future implementation will accept an optional Github token to allow lookup of private repositories.
  - A future implementation will accept an optional version to look up a specific release, which defaults to the latest if not provided.
options:
  repos:
    description: A list of Github repositories from which to retrieve versions.
    required: True
notes:
  - The version tag is returned however it is defined by the Github repository. Most repositories used the convention 'vX.X.X' for a tag, while some use 'X.X.X'. Some may use release tagging structures other than semver. This plugin does not perform opinionated formatting of the release tag structure. Users should format the value via filters after calling this plugin, if needed.
seealso:
  - name: Github Releases API
    description: API documentation for retrieving the latest version of a release.
    link: https://developer.github.com/v3/repos/releases/#get-the-latest-release
"""

EXAMPLES = r"""
- name: Strip the 'v' out of the tag version, e.g. 'v1.0.0' -> '1.0.0'
  set_fact:
    nvm_version: "{{ lookup('github_version', 'nvm-sh/nvm')[1:] }}"

- name: Operate on multiple repositories
  git:
    repo: https://github.com/{{ item }}.git
    version: "{{ lookup('github_version', item) }}"
    dest: "{{ lookup('env', 'HOME') }}/projects"
  with_items:
    - ansible/ansible
    - ansible/molecule
    - ansible/awx
"""

RETURN = r"""
  _list:
    description:
      - List of latest Github repository version(s)
    type: list
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils._text import to_native

from json import JSONDecodeError, loads
from re import compile as regex_compile
from urllib.error import URLError
from urllib.request import Request, urlopen

display = Display()


class LookupModule(LookupBase):

    def run(self, repos, variables=None, **kwargs):
        # lookups in general are expected to both take a list as input and output a list
        # this is done so they work with the looping construct 'with_'.
        versions = []

        if len(repos) == 0:
          raise AnsibleParserError("You must specify at least one repo name")

        for repo in repos:

            # https://regex101.com/r/CHm7eZ/1
            valid_github_username_and_repo_name = regex_compile(r'[a-z\d\-]+\/[a-z\d\S]+')
            if not repo or not valid_github_username_and_repo_name.match(repo):
                # The Parser error indicates invalid options passed
                raise AnsibleParserError("repo name is incorrectly formatted: %s" % repo)

            display.debug("Github version lookup term: '%s'" % repo)

            # Retrieve the Github API Releases JSON
            try:
                github_request = Request('https://api.github.com/repos/%s/releases/latest' % repo,
                headers={ 'Accept': 'application/vnd.github.v3+json' }
                )
                response = urlopen(github_request)
                json_response = loads(response.read().decode('utf-8'))

                version = json_response.get('tag_name')
                if version != None and len(version) != 0:
                    versions.append(version)
                else:
                    raise AnsibleError("Error extracting version from Github API response:\n%s" % github_request.text)
            # Any errors raised by the urllib library inherit from URLError
            except URLError as e:
                raise AnsibleError("Error communicating with the Github API: %s" % to_native(e))
            except JSONDecodeError as e:
                raise AnsibleError("Error parsing JSON from Github API response: %s" % to_native(e))

            display.vvvv(u"Github version lookup using %s as repo" % repo)


        return versions

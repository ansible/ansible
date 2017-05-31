# (c) 2013, Jinn Koriech <jinn.koriech@gmail.com>
# vim:set ts=4 sw=4 sts=4 expandtab:
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import ansible.errors as errors

def flatten(terms):
    ret = []
    for term, data in terms.iteritems():
        if isinstance(term, list):
            ret.extend(term)
        else:
            ret.append(data)
    return ret

class LookupModule(object):
    """
    Usage:
      - name: Create users
        user: ...
        with_merged:
            - "{{ users_default }}"
            - "{{ users_group_vars }}"

    Where YAML is:
      users_default:
        alice:
            uid: 5000
        basar:
            uid: 5001
        cuica:
            uid: 5002

      users_group_vars:
        alice:
            uid: 5003
        dalya:
            uid: 5004

    Merges the list of arrays:
        a = { "alice": { "uid": 5000 }, "basar": { "uid": 5001 } }
        b = { "cuica": { "uid": 5002 } }
        c = { "alice": { "uid": 5003 } }
        d = { "dalya": { "uid": 5004 } }
        thelist = [a, b, c, d]
        result = {}
        for thedict in thelist:
            result.update(thedict)
        ### the result ###
        #{'alice': {'uid': 5003},
        # 'basar': {'uid': 5001},
        # 'cuica': {'uid': 5002},
        # 'dalya': {'uid': 5004}}
    """

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, merge=None, **kwargs):
        if len(terms) == 0:
            raise errors.AnsibleError("with_merged requires at least one array in each list")

        results = {}
        for term in terms:
            # We silently ignore any items specified that are not dict().
            # This is necessary to handle merger when deeper vars are defined
            # in the tasks but not always defined in the vars.  The downside
            # is that if users don't define the YAML correctly this will
            # silently fail.  Ideally we'd be able to output some info when
            # running with at least one -v, but can't see how to implement that
            # now.
            if isinstance(term, dict):
                results.update(term)

        return flatten(results)

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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


def flatten(terms):
    ret = []
    for term in terms:
        if isinstance(term, list):
            ret.extend(term)
        elif isinstance(term, tuple):
            ret.extend(term)
        else:
            ret.append(term)
    return ret

def combine(a,b):
    results = []
    for x in a:
        for y in b:
            results.append([x,y])
    return results

class LookupModule(object):

    def __init__(self, **kwargs):
        pass

    def run(self, terms, **kwargs):
        if not isinstance(terms, list):
            raise errors.AnsibleError("a list is required for with_nested")
        my_list = terms[:]
        my_list.reverse()
        result = []
        if len(my_list) == 0:
            raise errors.AnsibleError("with_nested requires at least one list")
        result = my_list.pop()
        while len(my_list) > 0:
            result2 = combine(result, my_list.pop())
            result  = result2
        new_result = []
        for x in result:
            new_result.append(flatten(x))
        return new_result



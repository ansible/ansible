# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.utils.display import Display

display = Display()


def nochange(a):
    return a


def meaningoflife(a):
    return 42


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'noop': nochange,
            'ultimatequestion': meaningoflife,
            'b64decode': nochange,   # here to colide with basename of builtin
        }

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.utils.display import Display

display = Display()


def donothing(a):
    return a


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'donothing': donothing,
            'nodocs': donothing,
            'split': donothing,
            'b64decode': donothing,
        }

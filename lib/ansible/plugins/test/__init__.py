# (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing as t

from ansible.plugins import AnsibleJinja2Plugin


class AnsibleJinja2Test(AnsibleJinja2Plugin):
    @property
    def plugin_type(self) -> str:
        return "test"

    def _no_options(self, *args, **kwargs) -> t.NoReturn:
        raise NotImplementedError("Jinja2 test plugins do not support option functions, they use direct arguments instead.")

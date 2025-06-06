from __future__ import annotations as _annotations

import datetime as _datetime
import os as _os
import pwd as _pwd
import time as _time

from ansible import constants as _constants
from ansible.module_utils._internal import _datatag


def generate_ansible_template_vars(
    path: str,
    fullpath: str | None = None,
    dest_path: str | None = None,
    include_ansible_managed: bool = True,
) -> dict[str, object]:
    """
    Generate and return a dictionary with variable metadata about the template specified by `fullpath`.
    If `fullpath` is `None`, `path` will be used instead.
    """
    # deprecated description="update the ansible.windows collection to inline this logic instead of calling this internal function" core_version="2.23"
    if fullpath is None:
        fullpath = _os.path.abspath(path)

    template_path = fullpath
    template_stat = _os.stat(template_path)

    template_uid: int | str

    try:
        template_uid = _pwd.getpwuid(template_stat.st_uid).pw_name
    except KeyError:
        template_uid = template_stat.st_uid

    temp_vars = dict(
        template_host=_os.uname()[1],
        template_path=path,
        template_mtime=_datetime.datetime.fromtimestamp(template_stat.st_mtime),
        template_uid=template_uid,
        template_run_date=_datetime.datetime.now(),
        template_destpath=dest_path,
        template_fullpath=fullpath,
    )

    if include_ansible_managed:  # only inject the config default value if the variable wasn't set
        temp_vars['ansible_managed'] = _generate_ansible_managed(template_stat)

    return temp_vars


def _generate_ansible_managed(template_stat: _os.stat_result) -> str:
    """Generate and return the `ansible_managed` variable."""
    # deprecated description="remove the `_generate_ansible_managed` function and use a constant instead" core_version="2.23"

    from ansible.template import trust_as_template

    managed_default = _constants.config.get_config_value('DEFAULT_MANAGED_STR')

    managed_str = managed_default.format(
        # IMPORTANT: These values must be constant strings to avoid template injection.
        #            Use Jinja template expressions where variables are needed.
        host="{{ template_host }}",
        uid="{{ template_uid }}",
        file="{{ template_path }}",
    )

    ansible_managed = _time.strftime(managed_str, _time.localtime(template_stat.st_mtime))
    ansible_managed = _datatag.AnsibleTagHelper.tag_copy(managed_default, ansible_managed)
    ansible_managed = trust_as_template(ansible_managed)

    return ansible_managed

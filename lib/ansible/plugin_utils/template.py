from __future__ import annotations

import datetime
import os
import pwd
import time

from ansible import constants
from ansible.module_utils._internal import _datatag
from ansible.module_utils.datatag import deprecate_value
from ansible.utils.datatag import trust_value


def generate_ansible_template_vars(path: str, *, full_path: str | None = None, dest_path: str | None = None) -> dict[str, object]:
    """Generate and return a dictionary of template variables for the template specified by `path`."""
    # DTFIX-MERGE: should this reside here or in the template module?
    # DTFIX-MERGE: needs compat API in template (reminder -- the method sig has changed)
    if full_path is None:
        full_path = os.path.abspath(path)

    template_path = full_path
    template_stat = os.stat(template_path)

    template_uid: int | str

    try:
        template_uid = pwd.getpwuid(template_stat.st_uid).pw_name
    except KeyError:
        template_uid = template_stat.st_uid

    managed_default = constants.config.get_config_value('DEFAULT_MANAGED_STR')

    managed_str = managed_default.format(
        # IMPORTANT: These values must be constant strings to avoid template injection.
        #            Use Jinja template expressions where variables are needed.
        host="{{ template_host }}",
        uid="{{ template_uid }}",
        file="{{ template_path }}",
    )

    ansible_managed = time.strftime(managed_str, time.localtime(template_stat.st_mtime))
    # DTFIX-MERGE: should this just be copy_origin?
    ansible_managed = _datatag.AnsibleTagHelper.tag_copy(managed_default, ansible_managed)
    ansible_managed = trust_value(ansible_managed)
    # DTFIX-MERGE: why no help_text on deprecated tags?
    ansible_managed = deprecate_value(ansible_managed, "The `ansible_managed` variable is deprecated.", removal_version='2.23')

    temp_vars = dict(
        template_host=os.uname()[1],
        template_path=path,
        template_mtime=datetime.datetime.fromtimestamp(template_stat.st_mtime),
        template_uid=template_uid,
        template_run_date=datetime.datetime.now(),
        template_destpath=dest_path,
        template_fullpath=full_path,
        ansible_managed=ansible_managed,
    )

    return temp_vars

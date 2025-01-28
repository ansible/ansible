from __future__ import annotations

import datetime
import os
import pwd
import time

from ansible import constants
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.module_utils.datatag import AnsibleTagHelper
from ansible.utils.datatag.tags import TrustedAsTemplate


def generate_ansible_template_vars(path, fullpath=None, dest_path=None):

    if fullpath is None:
        b_path = to_bytes(path)
    else:
        b_path = to_bytes(fullpath)

    try:
        template_uid = pwd.getpwuid(os.stat(b_path).st_uid).pw_name
    except (KeyError, TypeError):
        template_uid = os.stat(b_path).st_uid

    temp_vars = {
        'template_host': to_text(os.uname()[1]),
        'template_path': path,
        'template_mtime': datetime.datetime.fromtimestamp(os.path.getmtime(b_path)),
        'template_uid': to_text(template_uid),
        'template_run_date': datetime.datetime.now(),
        'template_destpath': to_native(dest_path) if dest_path else None,
    }

    if fullpath is None:
        temp_vars['template_fullpath'] = os.path.abspath(path)
    else:
        temp_vars['template_fullpath'] = fullpath

    managed_default = constants.config.get_config_value('DEFAULT_MANAGED_STR')

    # DTFIX-MERGE: deprecate this in favor of users defining their own variable to replace ansible_managed
    #        to make the transition easier, there should be a facility to define custom variables (with templates) in config
    managed_str = managed_default.format(
        # IMPORTANT: These values must be constant strings to avoid template injection.
        #            Use Jinja template expressions where variables are needed.
        host="{{ template_host }}",
        uid="{{ template_uid }}",
        file="{{ template_path }}",
    )

    temp_vars['ansible_managed'] = AnsibleTagHelper.tag_copy(managed_default, time.strftime(managed_str, time.localtime(os.path.getmtime(b_path))))

    # DTFIX-FUTURE: some config values should be trusted as templates -- config should be able to decide that
    #        once config provides a trusted value, this can be removed and the trust will be preserved by the tag_copy above
    temp_vars['ansible_managed'] = TrustedAsTemplate().tag(temp_vars['ansible_managed'])

    return temp_vars

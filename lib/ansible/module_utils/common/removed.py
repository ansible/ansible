# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from ansible.module_utils._text import to_text


def removed_module(msg=u'This module has been removed.  The module documentation may contain hints for porting'):
    """
    When a module is removed, we want the documentation available for a few releases to aid in
    porting playbooks.  So leave the documentation but remove the actual code and instead have this
    boilerplate::

        from ansible.module_utils.common.removed import removed_module

        if __name__ == '__main__':
            removed_module()
    """
    # We may not have an AnsibleModule when this is called
    msg = to_text(msg).translate({ord(u'"'): u'\\"'})
    print('\n{{"msg": "{0}", "failed": true}}'.format(msg))

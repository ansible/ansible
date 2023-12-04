# -*- coding: utf-8 -*-

# Copyright: (c) 2018, John Barker <gundalow@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  follow_redirects:
    description:
      - Whether or not redirects should be followed. V(all) will follow all redirects.
        V(safe) will follow only "safe" redirects, where "safe" means that the client is only
        doing a GET or HEAD on the URI to which it is being redirected. V(none) will not follow
        any redirects. Note that V(true) and V(false) choices are accepted for backwards compatibility,
        where V(true) is the equivalent of V(all) and V(false) is the equivalent of V(safe). V(true) and V(false)
        are deprecated and will be removed in some future version of Ansible.
    type: str
    choices: ['all', 'no', 'none', 'safe', 'urllib2', 'yes']
    default: safe
'''

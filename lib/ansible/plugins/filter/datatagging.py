# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.errors import AnsibleOptionsError
from ansible._internal._datatag._tags import Origin, VaultedValue, SourceWasEncrypted, TrustedAsTemplate
from ansible.module_utils._internal._datatag import AnsibleTagHelper

_TAGS = {
    'trust': TrustedAsTemplate,
    'encrypted': SourceWasEncrypted,
    'origin': Origin,
    'vault': VaultedValue,
}


def do_origin(data, origin=Origin.UNKNOWN):
    return AnsibleTagHelper.tag(data, Origin(description=f'Origin filter: {origin}'))


def do_tag(data, tag):
    try:
        return _TAGS[tag]().tag(data)
    except KeyError:
        raise AnsibleOptionsError(f"The tag filter received invalid option {tag}, valid options are: encrypted, trust and vault.")


def do_trust(data):
    if not TrustedAsTemplate.is_tagged_on(data):
        data = TrustedAsTemplate().tag(data)
    return data


def do_untag(data, tag):
    try:
        return AnsibleTagHelper.untag(data, _TAGS[tag])
    except KeyError:
        raise AnsibleOptionsError(f"The untag filter received invalid option {tag}, valid options are: encrypted, origin, trust and vault.")


def do_untrust(data):
    return AnsibleTagHelper.untag(data, TrustedAsTemplate)


class FilterModule(object):
    """ Ansible Jinja filters """
    def filters(self):
        filters = {
            # specific
            'origin': do_origin,
            'unsafe': do_untrust,
            'trusted': do_trust,
            # generic
            'tag': do_tag,
            'untag': do_untag,
        }
        return filters

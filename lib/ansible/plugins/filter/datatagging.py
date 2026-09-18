# Copyright: (c) 2021, Ansible Project

from __future__ import annotations

from ansible.errors import AnsibleOptionsError
from ansible._internal._datatag._tags import Origin, VaultedValue, SourceWasEncrypted, TrustedAsTemplate
from ansible.module_utils._internal._datatag import AnsibleTagHelper


def do_origin(data, origin=Origin.UNKNOWN):
    return AnsibleTagHelper.tag(data, Origin(description=f'Origin filter: {origin}'))


def do_tag(data, tag):
    match tag:
        case 'trust':
            data = TrustedAsTemplate().tag(data)
        case 'encrypted':
            data = SourceWasEncrypted().tag(data)
        case 'vault':
            data = VaultedValue().tag(data)
        case _:
            raise AnsibleOptionsError(f"The tag filter received invalid option {tag}, valid options are: encrypted, trust and vault.")
    return data


def do_trust(data):
    if not TrustedAsTemplate.is_tagged_on(data):
        data = TrustedAsTemplate().tag(data)
    return data


def do_untag(data, tag):
    match tag:
        case 'trust':
            data = AnsibleTagHelper.untag(data, TrustedAsTemplate)
        case 'encrypted':
            data = AnsibleTagHelper.untag(data, SourceWasEncrypted)
        case 'origin':
            data = AnsibleTagHelper.untag(data, Origin)
        case 'vault':
            data = AnsibleTagHelper.untag(data, VaultedValue)
        case _:
            raise AnsibleOptionsError(f"The untag filter received invalid option {tag}, valid options are: encrypted, origin, trust and vault.")
    return AnsibleTagHelper.untag(data)


def do_untrust(data):
    return AnsibleTagHelper.untag(data, TrustedAsTemplate)


class FilterModule(object):
    """ Ansible Jinja filters """
    def filters(self):
        filters = {
            'origin': do_origin,
            'suspect': do_untrust,
            'tag': do_tag,
            'trust': do_trust,
            'untag': do_untag,
        }
        return filters

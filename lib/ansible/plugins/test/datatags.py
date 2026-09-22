# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations
from ansible._internal._datatag._tags import Origin, VaultedValue, SourceWasEncrypted, TrustedAsTemplate


def is_trusted(data):
    return TrustedAsTemplate.is_tagged_on(data)


def match_origin(data, origin=Origin.UNKNOWN):
    return origin == str(Origin.get_tag(data))


def not_is_trusted(data):
    return not is_trusted(data)


def was_encrypted(data):
    return SourceWasEncrypted.is_tagged_on(data)


class TestModule(object):
    def tests(self):
        return {
            'encrypted': was_encrypted,
            'origin': match_origin,
            'trusted': is_trusted,
            'unsafe': not_is_trusted,
        }

# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Sam Doran <sdoran@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader


@pytest.mark.parametrize(
    ('kwargs', 'agent'),
    (
        ({}, 'ansible-httpget'),
        ({'http_agent': 'SuperFox'}, 'SuperFox'),
    )
)
def test_user_agent(mocker, kwargs, agent):
    mock_open_url = mocker.patch('ansible.plugins.lookup.url.open_url', side_effect=AttributeError('raised intentionally'))
    url_lookup = lookup_loader.get('url')
    with pytest.raises(AttributeError):
        url_lookup.run(['https://nourl'], **kwargs)
    assert 'http_agent' in mock_open_url.call_args.kwargs
    assert mock_open_url.call_args.kwargs['http_agent'] == agent

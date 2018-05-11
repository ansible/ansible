# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.urls import generic_urlparse
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlunparse


def test_generic_urlparse():
    url = 'https://ansible.com/blog'
    parts = urlparse(url)
    generic_parts = generic_urlparse(parts)
    assert generic_parts.as_list() == list(parts)

    assert urlunparse(generic_parts.as_list()) == url


def test_generic_urlparse_netloc():
    url = 'https://ansible.com:443/blog'
    parts = urlparse(url)
    generic_parts = generic_urlparse(parts)
    assert generic_parts.hostname == parts.hostname
    assert generic_parts.hostname == 'ansible.com'
    assert generic_parts.port == 443
    assert urlunparse(generic_parts.as_list()) == url


def test_generic_urlparse_no_netloc():
    url = 'https://user:passwd@ansible.com:443/blog'
    parts = list(urlparse(url))
    generic_parts = generic_urlparse(parts)
    assert generic_parts.hostname == 'ansible.com'
    assert generic_parts.port == 443
    assert generic_parts.username == 'user'
    assert generic_parts.password == 'passwd'
    assert urlunparse(generic_parts.as_list()) == url


def test_generic_urlparse_no_netloc_no_auth():
    url = 'https://ansible.com:443/blog'
    parts = list(urlparse(url))
    generic_parts = generic_urlparse(parts)
    assert generic_parts.username is None
    assert generic_parts.password is None


def test_generic_urlparse_no_netloc_no_host():
    url = '/blog'
    parts = list(urlparse(url))
    generic_parts = generic_urlparse(parts)
    assert generic_parts.username is None
    assert generic_parts.password is None
    assert generic_parts.port is None
    assert generic_parts.hostname == ''

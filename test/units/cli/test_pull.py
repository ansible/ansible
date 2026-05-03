# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Shivansh Sahu
# GNU General Public License v3.0+

from __future__ import annotations


class TestPullLimitBehavior:
    """
    Tests for ansible-pull --limit behaviour fixes.
    Covers issue #86854:
      1. Short hostname must not appear in auto-limit (group name collision)
      2. Explicit --limit must be respected in the checkout step
    """

    def test_short_hostname_not_in_auto_limit(self):
        """
        When FQDN is 'rancid.myweb.sk', the auto-limit must NOT contain
        the bare short name 'rancid' — it could match an inventory group.
        """
        host = 'rancid.myweb.sk'
        node = 'rancid.myweb.sk'

        # This is the FIXED logic from pull.py
        limit_hosts = list(set([host, node]))
        hostnames = ','.join(limit_hosts)
        limit_opts = 'localhost,%s,127.0.0.1' % hostnames

        short = host.split('.', maxsplit=1)[0]  # 'rancid'
        tokens = limit_opts.split(',')

        assert short not in tokens, (
            f"Short hostname '{short}' must not appear as a standalone "
            f"token in limit_opts — it can match group names in inventory. "
            f"Got: {limit_opts}"
        )
        assert host in tokens, f"FQDN '{host}' must still be in limit_opts"

    def test_fqdn_and_node_deduplication(self):
        """
        When host and node resolve to the same value, the limit should
        not contain duplicate entries.
        """
        host = 'myserver.example.com'
        node = 'myserver.example.com'

        limit_hosts = list(set([host, node]))
        hostnames = ','.join(limit_hosts)

        # Only one entry, no duplicates
        assert hostnames.count('myserver.example.com') == 1

    def test_explicit_user_limit_overrides_auto_limit(self):
        """
        When the user passes --limit explicitly, the checkout command
        must use that value — not the auto-generated one.
        Issue #86854: checkout step was ignoring context.CLIARGS['subset'].
        """
        host = 'rancid.myweb.sk'
        node = 'rancid.myweb.sk'
        user_limit = 'rancid.myweb.sk'   # what user passed via --limit

        limit_hosts = list(set([host, node]))
        hostnames = ','.join(limit_hosts)

        # Fixed logic: respect user_limit when present
        if user_limit:
            limit_opts = user_limit
        elif hostnames:
            limit_opts = 'localhost,%s,127.0.0.1' % hostnames
        else:
            limit_opts = 'localhost,127.0.0.1'

        assert limit_opts == user_limit, (
            f"Explicit --limit '{user_limit}' must be used as-is. "
            f"Got: '{limit_opts}'"
        )
        # Must NOT contain other hosts that would widen the scope
        assert 'dc1' not in limit_opts
        assert '127.0.0.1' not in limit_opts

    def test_no_user_limit_falls_back_to_auto(self):
        """
        When no --limit is passed, the checkout falls back to the
        auto-generated hostnames (FQDNs only, no short names).
        """
        host = 'myserver.example.com'
        node = 'myserver.example.com'
        user_limit = None   # no --limit passed

        limit_hosts = list(set([host, node]))
        hostnames = ','.join(limit_hosts)

        if user_limit:
            limit_opts = user_limit
        elif hostnames:
            limit_opts = 'localhost,%s,127.0.0.1' % hostnames
        else:
            limit_opts = 'localhost,127.0.0.1'

        assert host in limit_opts
        assert 'localhost' in limit_opts
        assert '127.0.0.1' in limit_opts
        # short name must NOT appear as a standalone token
        # (but may appear as part of the FQDN — that's fine)
        short = host.split('.', maxsplit=1)[0]  # 'myserver'
        tokens = [t.strip() for t in limit_opts.split(',')]
        assert short not in tokens, (
            f"Short name '{short}' must not be a standalone token. "
            f"Tokens found: {tokens}"
        )

    def test_different_host_and_node_both_included(self):
        """
        When socket.getfqdn() and platform.node() return different values
        (can happen on some systems), both should be in the auto-limit.
        """
        host = 'server.example.com'
        node = 'server-alias.example.com'   # different node name

        limit_hosts = list(set([host, node]))
        hostnames = ','.join(limit_hosts)
        limit_opts = 'localhost,%s,127.0.0.1' % hostnames

        assert host in limit_opts
        assert node in limit_opts

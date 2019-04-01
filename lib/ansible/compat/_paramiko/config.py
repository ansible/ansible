# Copyright (C) 2006-2007  Robey Pointer <robeypointer@gmail.com>
# Copyright (C) 2012  Olle Lundberg <geek@nerd.sh>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
Configuration file (aka ``ssh_config``) support.
"""

import fnmatch
import os
import re
import shlex
import socket

SSH_PORT = 22


class SSHConfig(object):
    """
    Representation of config information as stored in the format used by
    OpenSSH. Queries can be made via `lookup`. The format is described in
    OpenSSH's ``ssh_config`` man page. This class is provided primarily as a
    convenience to posix users (since the OpenSSH format is a de-facto
    standard on posix) but should work fine on Windows too.

    .. versionadded:: 1.6
    """

    SETTINGS_REGEX = re.compile(r"(\w+)(?:\s*=\s*|\s+)(.+)")

    def __init__(self):
        """
        Create a new OpenSSH config object.
        """
        self._config = []

    def parse(self, file_obj):
        """
        Read an OpenSSH config from the given file object.

        :param file_obj: a file-like object to read the config file from
        """
        host = {"host": ["*"], "config": {}}
        for line in file_obj:
            # Strip any leading or trailing whitespace from the line.
            # Refer to https://github.com/paramiko/paramiko/issues/499
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(self.SETTINGS_REGEX, line)
            if not match:
                raise Exception("Unparsable line {}".format(line))
            key = match.group(1).lower()
            value = match.group(2)

            if key == "host":
                self._config.append(host)
                host = {"host": self._get_hosts(value), "config": {}}
            elif key == "proxycommand" and value.lower() == "none":
                # Store 'none' as None; prior to 3.x, it will get stripped out
                # at the end (for compatibility with issue #415). After 3.x, it
                # will simply not get stripped, leaving a nice explicit marker.
                host["config"][key] = None
            else:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]

                # identityfile, localforward, remoteforward keys are special
                # cases, since they are allowed to be specified multiple times
                # and they should be tried in order of specification.
                if key in ["identityfile", "localforward", "remoteforward"]:
                    if key in host["config"]:
                        host["config"][key].append(value)
                    else:
                        host["config"][key] = [value]
                elif key not in host["config"]:
                    host["config"][key] = value
        self._config.append(host)

    def lookup(self, hostname):
        """
        Return a dict of config options for a given hostname.

        The host-matching rules of OpenSSH's ``ssh_config`` man page are used:
        For each parameter, the first obtained value will be used.  The
        configuration files contain sections separated by ``Host``
        specifications, and that section is only applied for hosts that match
        one of the patterns given in the specification.

        Since the first obtained value for each parameter is used, more host-
        specific declarations should be given near the beginning of the file,
        and general defaults at the end.

        The keys in the returned dict are all normalized to lowercase (look for
        ``"port"``, not ``"Port"``. The values are processed according to the
        rules for substitution variable expansion in ``ssh_config``.

        :param str hostname: the hostname to lookup
        """
        matches = [
            config
            for config in self._config
            if self._allowed(config["host"], hostname)
        ]

        ret = {}
        for match in matches:
            for key, value in match["config"].items():
                if key not in ret:
                    # Create a copy of the original value,
                    # else it will reference the original list
                    # in self._config and update that value too
                    # when the extend() is being called.
                    ret[key] = value[:] if value is not None else value
                elif key == "identityfile":
                    ret[key].extend(value)
        ret = self._expand_variables(ret, hostname)
        # TODO: remove in 3.x re #670
        if "proxycommand" in ret and ret["proxycommand"] is None:
            del ret["proxycommand"]
        return ret

    def get_hostnames(self):
        """
        Return the set of literal hostnames defined in the SSH config (both
        explicit hostnames and wildcard entries).
        """
        hosts = set()
        for entry in self._config:
            hosts.update(entry["host"])
        return hosts

    def _allowed(self, hosts, hostname):
        match = False
        for host in hosts:
            if host.startswith("!") and fnmatch.fnmatch(hostname, host[1:]):
                return False
            elif fnmatch.fnmatch(hostname, host):
                match = True
        return match

    def _expand_variables(self, config, hostname):
        """
        Return a dict of config options with expanded substitutions
        for a given hostname.

        Please refer to man ``ssh_config`` for the parameters that
        are replaced.

        :param dict config: the config for the hostname
        :param str hostname: the hostname that the config belongs to
        """

        if "hostname" in config:
            config["hostname"] = config["hostname"].replace("%h", hostname)
        else:
            config["hostname"] = hostname

        if "port" in config:
            port = config["port"]
        else:
            port = SSH_PORT

        user = os.getenv("USER")
        if "user" in config:
            remoteuser = config["user"]
        else:
            remoteuser = user

        host = socket.gethostname().split(".")[0]
        fqdn = LazyFqdn(config, host)
        homedir = os.path.expanduser("~")
        replacements = {
            "controlpath": [
                ("%h", config["hostname"]),
                ("%l", fqdn),
                ("%L", host),
                ("%n", hostname),
                ("%p", port),
                ("%r", remoteuser),
                ("%u", user),
            ],
            "identityfile": [
                ("~", homedir),
                ("%d", homedir),
                ("%h", config["hostname"]),
                ("%l", fqdn),
                ("%u", user),
                ("%r", remoteuser),
            ],
            "proxycommand": [
                ("~", homedir),
                ("%h", config["hostname"]),
                ("%p", port),
                ("%r", remoteuser),
            ],
        }

        for k in config:
            if config[k] is None:
                continue
            if k in replacements:
                for find, replace in replacements[k]:
                    if isinstance(config[k], list):
                        for item in range(len(config[k])):
                            if find in config[k][item]:
                                config[k][item] = config[k][item].replace(
                                    find, str(replace)
                                )
                    else:
                        if find in config[k]:
                            config[k] = config[k].replace(find, str(replace))
        return config

    def _get_hosts(self, host):
        """
        Return a list of host_names from host value.
        """
        try:
            return shlex.split(host)
        except ValueError:
            raise Exception("Unparsable host {}".format(host))


class LazyFqdn(object):
    """
    Returns the host's fqdn on request as string.
    """

    def __init__(self, config, host=None):
        self.fqdn = None
        self.config = config
        self.host = host

    def __str__(self):
        if self.fqdn is None:
            #
            # If the SSH config contains AddressFamily, use that when
            # determining  the local host's FQDN. Using socket.getfqdn() from
            # the standard library is the most general solution, but can
            # result in noticeable delays on some platforms when IPv6 is
            # misconfigured or not available, as it calls getaddrinfo with no
            # address family specified, so both IPv4 and IPv6 are checked.
            #

            # Handle specific option
            fqdn = None
            address_family = self.config.get("addressfamily", "any").lower()
            if address_family != "any":
                try:
                    family = socket.AF_INET6
                    if address_family == "inet":
                        socket.AF_INET
                    results = socket.getaddrinfo(
                        self.host,
                        None,
                        family,
                        socket.SOCK_DGRAM,
                        socket.IPPROTO_IP,
                        socket.AI_CANONNAME,
                    )
                    for res in results:
                        af, socktype, proto, canonname, sa = res
                        if canonname and "." in canonname:
                            fqdn = canonname
                            break
                # giaerror -> socket.getaddrinfo() can't resolve self.host
                # (which is from socket.gethostname()). Fall back to the
                # getfqdn() call below.
                except socket.gaierror:
                    pass
            # Handle 'any' / unspecified
            if fqdn is None:
                fqdn = socket.getfqdn()
            # Cache
            self.fqdn = fqdn
        return self.fqdn

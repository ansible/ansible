#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Silvie Chlupova <schlupov@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: copr
author: Silvie Chlupova (schlupov@redhat.com)
version_added: 2.10
short_description: Manage one of the Copr repositories
description: This module can enable, disable or remove the specified repository.
options:
    host:
        description: The Copr host to work with
        default: copr.fedorainfracloud.org
        required: false
        type: str
    protocol:
        description: This indicate which protocol to use with the host.
        default: https
        required: false
        type: str
    name:
        description: Copr directory name, for example @copr/copr-dev.
        required: true
        type: str
    state:
        description:
            - Whether to set this project as "enabled", "disabled" or "absent".
              If unset, this defaults to "enabled".
        default: enabled
        required: false
        type: str
        choices: [absent, enabled, disabled]
    chroot:
        description: 
            - The name of the chroot that you want to enable/disable/remove in the project, e.g. epel-7-x86_64.
              Default chroot is determined by the operating system, version of the operating system, 
              and architecture on which the module is run.
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Enable Copr repository
  hosts: localhost
  tasks:
    - name: Enable project Test of the user schlupov
      copr:
        host: copr.fedorainfracloud.org
        state: enabled
        name: schlupov/Test
        chroot: fedora-31-x86_64
"""

import stat
import os
from urllib import request
from urllib import error
from pathlib import Path
import dnf
import dnf.cli
import dnf.repodict
from dnf.conf import Conf
from dnfpluginscore import _, logger
from ansible.module_utils import distro # pylint: disable=import-error
from ansible.module_utils.basic import AnsibleModule # pylint: disable=import-error


class CoprModule:
    """The class represents a copr module.

    The class contains methods that take care of the repository state of a project,
    whether the project is enabled, disabled or missing.
    """

    ansible_module = None

    def __init__(self, host, name, state, protocol, chroot=None):
        self.host = host
        self.name = name
        self.state = state
        self.chroot = chroot
        self.protocol = protocol
        if not chroot:
            self.chroot = self.chroot_conf()
        else:
            self.chroot = chroot
            self.get_base()

    @property
    def short_chroot(self):
        """str: Chroot (distribution-version-architecture) shorten to distribution-version."""
        chroot_parts = self.chroot.split("-")
        return f"{chroot_parts[0]}-{chroot_parts[1]}"

    @property
    def arch(self):
        """str: Target architecture."""
        chroot_parts = self.chroot.split("-")
        return chroot_parts[-1]

    @property
    def user(self):
        """str: Copr user (this can also be the name of the group)."""
        return self._sanitize_username(self.name.split("/")[0])

    @property
    def project(self):
        """str: The name of the copr project."""
        return self.name.split("/")[1]

    @classmethod
    def need_root(cls):
        """Check if the module was run as root."""
        if os.geteuid() != 0:
            cls.raise_exception("This command has to be run under the root user.")

    @classmethod
    def get_base(cls):
        """Initialize the configuration from dnf.

        Returns:
            An instance of the BaseCli class.
        """
        cls.base = dnf.cli.cli.BaseCli(Conf())
        return cls.base

    @classmethod
    def raise_exception(cls, msg):
        """Raise either an ansible exception or a python exception.

        Args:
            msg: The message to be displayed when an exception is thrown.
        """
        if cls.ansible_module:
            raise cls.ansible_module.fail_json(msg=msg, changed=False)
        raise Exception(msg)

    def _get(self, chroot):
        """Send a get request to the server to obtain the necessary data.

        Args:
            chroot: Chroot in the form of distribution-version.

        Returns:
            Info about a repository and status code of the get request.
        """
        repo_info = None
        url = (
            f"{self.protocol}://{self.host}/coprs/{self.name}/"
            f"repo/{chroot}/dnf.repo?arch={self.arch}"
        )
        try:
            r = request.urlopen(url)
            status_code = r.getcode()
            repo_info = r.read().decode("utf-8")
        except error.HTTPError as e:
            status_code = e.getcode()
        return repo_info, status_code

    def _download_repo_info(self):
        """Download information about the repository.

        Returns:
            Information about the repository.
        """
        distribution, version = self.short_chroot.split("-")
        chroot = self.short_chroot
        while True:
            repo_info, status_code = self._get(chroot)
            if repo_info:
                return repo_info
            if distribution == "rhel":
                chroot = "centos-stream"
                distribution = "centos"
            elif distribution == "centos":
                if version == "stream":
                    version = "8"
                chroot = f"epel-{version}"
                distribution = "epel"
            else:
                if str(status_code) != "404":
                    self.raise_exception(
                        "This repository does not have any builds yet so you cannot enable it now."
                    )
                else:
                    self.raise_exception(f"Chroot {self.chroot} does not exist in {self.name}")

    def _enable_repo(self, repo_filename_path, repo_content=None):
        """Write information to a repo file.

        Args:
            repo_filename_path: Path to repository.
            repo_content: Repository information from the host.

        Returns:
            True, if the information in the repo file matches that stored on the host,
            False otherwise.
        """
        if not repo_content:
            repo_content = self._download_repo_info()
        if self._compare_repo_content(repo_filename_path, repo_content):
            if not self.ansible_module:
                logger.info(_("Repository already enabled."))
            return False
        with open(repo_filename_path, "w+") as file:
            file.write(repo_content)
        os.chmod(
            repo_filename_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
        )
        if not self.ansible_module:
            logger.info(_("Repository successfully enabled."))
        return True

    def _get_repo_with_old_id(self):
        """Try to get a repository with the old name."""
        repo_id = f"{self.user}-{self.project}"
        if repo_id in self.base.repos and "_copr" in self.base.repos[repo_id].repofile:
            file_name = self.base.repos[repo_id].repofile.split("/")[-1]
            try:
                copr_hostname = file_name.rsplit(":", 2)[0].split(":", 1)[1]
                if copr_hostname != self.host:
                    return None
                return file_name
            except IndexError:
                return file_name
        return None

    def _read_all_repos(self, repo_id=None):
        """The method is used to initialize the base variable by
        repositories using the RepoReader class from dnf.

        Args:
            repo_id: Repo id of the repository we want to work with.
        """
        reader = dnf.conf.read.RepoReader(self.base.conf, None)
        for repo in reader:
            try:
                if repo_id:
                    if repo.id == repo_id:
                        self.base.repos.add(repo)
                        break
                else:
                    self.base.repos.add(repo)
            except dnf.exceptions.ConfigError as e:
                self.raise_exception(str(e))

    def _get_copr_repo(self):
        """Return one specific repository from all repositories on the system.

        Returns:
            The repository that a user wants to enable, disable, or remove.
        """
        repo_id = f"copr:{self.host}:{self.user}:{self.project}"
        if repo_id not in self.base.repos:
            if self._get_repo_with_old_id() is None:
                return None
        return self.base.repos[repo_id]

    def _disable_repo(self, repo_filename_path):
        """Disable the repository.

        Args:
            repo_filename_path: Path to repository.

        Returns:
            False, if the repository is already disabled on the system,
            True otherwise.
        """
        self._read_all_repos()
        repo = self._get_copr_repo()
        if repo is None:
            self._enable_repo(repo_filename_path)
            self._read_all_repos(f"copr:{self.host}:{self.user}:{self.project}")
            repo = self._get_copr_repo()
        for repo_id in repo.cfg.sections():
            repo_content_api = self._download_repo_info()
            with open(repo_filename_path, "r") as file:
                repo_content_file = file.read()
            if repo_content_file != repo_content_api:
                if not self.resolve_differences(repo_content_file, repo_content_api, repo_filename_path):
                    return False
            self.base.conf.write_raw_configfile(
                repo.repofile, repo_id, self.base.conf.substitutions, {"enabled": "0"},
            )
        return True

    def resolve_differences(self, repo_content_file, repo_content_api, repo_filename_path):
        """Detect differences between the contents of the repository stored on the
        system and the information about the repository on the server.

        Args:
            repo_content_file: The contents of the repository stored on the system.
            repo_content_api: The information about the repository from the server.
            repo_filename_path: Path to repository.

        Returns:
            False, if the contents of the repo file and the information on the server match,
            True otherwise.
        """
        repo_file_lines = repo_content_file.split("\n")
        repo_api_lines = repo_content_api.split("\n")
        repo_api_lines.remove("enabled=1")
        if "enabled=0" in repo_file_lines:
            repo_file_lines.remove("enabled=0")
            if " ".join(repo_api_lines) == " ".join(repo_file_lines):
                return False
            os.remove(repo_filename_path)
            self._enable_repo(repo_filename_path, repo_content_api)
        else:
            repo_file_lines.remove("enabled=1")
            if " ".join(repo_api_lines) != " ".join(repo_file_lines):
                os.remove(repo_filename_path)
                self._enable_repo(repo_filename_path, repo_content_api)
        return True

    def _remove_repo(self):
        """Remove the required repository.

        Returns:
            True, if the repository has been removed, False otherwise.
        """
        self._read_all_repos()
        repo = self._get_copr_repo()
        if not repo:
            return False
        try:
            os.remove(repo.repofile)
            return True
        except OSError as e:
            self.raise_exception(str(e))

    def run(self):
        """The method uses methods of the CoprModule class to change the state of the repository.

        Returns:
            Dictionary with information that the ansible module displays to the user at the end of the run.
        """
        self.need_root()
        state = dict()
        repo_filename = f"_copr:{self.host}:{self.user}:{self.project}.repo"
        state["repo"] = f"{self.host}/{self.user}/{self.project}"
        state["repo_filename"] = repo_filename
        repo_filename_path = (
            f"{self.base.conf.get_reposdir}/_copr:{self.host}:{self.user}:{self.project}.repo"
        )
        if self.state == "enabled":
            enabled = self._enable_repo(repo_filename_path)
            state["msg"] = "enabled"
            state["state"] = bool(enabled)
        elif self.state == "disabled":
            disabled = self._disable_repo(repo_filename_path)
            state["msg"] = "disabled"
            state["state"] = bool(disabled)
        elif self.state == "absent":
            removed = self._remove_repo()
            state["msg"] = "absent"
            state["state"] = bool(removed)
        return state

    @staticmethod
    def _compare_repo_content(repo_filename_path, repo_content_api):
        """Compare the contents of the stored repository with the information from the server.

        Args:
            repo_filename_path: Path to repository.
            repo_content_api: The information about the repository from the server.

        Returns:
            True, if the information matches, False otherwise.
        """
        copr_repo_file = Path(repo_filename_path)
        if not copr_repo_file.is_file():
            return False
        with open(repo_filename_path, "r") as file:
            repo_content_file = file.read()
        return repo_content_file == repo_content_api

    @staticmethod
    def chroot_conf():
        """Obtain information about the distribution, version, and architecture of the target.

        Returns:
            Chroot info in the form of distribution-version-architecture.
        """
        (distribution, version, _) = distro.linux_distribution(full_distribution_name=False)
        base = CoprModule.get_base()
        return f"{distribution}-{version}-{base.conf.arch}"

    @staticmethod
    def _sanitize_username(user):
        """Modify the group name.

        Args:
            user: User name.

        Returns:
            Modified user name if it is a group name with @.
        """
        if user[0] == "@":
            return f"group_{user[1:]}"
        return user


def run_module():
    """The function takes care of the functioning of the whole ansible copr module."""
    module_args = dict(
        host=dict(type="str", default="copr.fedorainfracloud.org"),
        protocol=dict(type="str", default="https"),
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["enabled", "disabled", "absent"], default="enabled"),
        chroot=dict(type="str", required=False),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    params = module.params

    result = dict(
        host=params["host"],
        protocol=params["protocol"],
        name=params["name"],
        state=params["state"],
        chroot=params["chroot"],
    )

    if module.check_mode:
        module.exit_json(**result)

    CoprModule.ansible_module = module
    copr_module = CoprModule(
        host=params["host"],
        name=params["name"],
        state=params["state"],
        protocol=params["protocol"],
        chroot=params["chroot"],
    )
    state = copr_module.run()

    info = "Please note that this repository is not part of the main distribution"

    if params["state"] == "enabled" and state["state"]:
        module.exit_json(
            changed=state["state"],
            msg=state["msg"],
            repo=state["repo"],
            repo_filename=state["repo_filename"],
            info=info,
        )
    module.exit_json(
        changed=state["state"],
        msg=state["msg"],
        repo=state["repo"],
        repo_filename=state["repo_filename"],
    )


def main():
    """Launches ansible Copr module."""
    run_module()


if __name__ == "__main__":
    main()

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.system.env import EnvFactCollector


class TestEnvFacts:
    def test_os_env(self, monkeypatch):
        monkeypatch.setenv("debian_chroot", "test")
        env_facts = EnvFactCollector().collect()
        assert env_facts["env"]["debian_chroot"] == "test"

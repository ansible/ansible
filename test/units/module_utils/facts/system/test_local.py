# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from os import stat_result

from ansible.module_utils.facts.system.local import LocalFactCollector


class TestLocalFacts:
    def test_local_no_module(self):
        local_facts = LocalFactCollector().collect()
        assert local_facts == {"local": {}}

    def test_local_no_fact_path_exists(self, mocker):
        module = mocker.Mock()
        mocker.patch("os.path.exists", return_value=False)
        local_facts = LocalFactCollector().collect(module=module)
        assert local_facts == {"local": {}}

    def test_local_facts(self, mocker):
        module = mocker.MagicMock()
        module.params = {"fact_path": "/usr/local/facts"}
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("glob.glob", return_value=["/usr/local/facts/sample.fact"])
        local_facts = LocalFactCollector().collect(module=module)
        assert "Could not stat fact" in local_facts["local"]["sample"]

        mock_stat = stat_result([mocker.MagicMock()] * 10)
        mocker.patch("os.stat", return_value=mock_stat)
        mocker.patch.object(module, "run_command", return_value=(1, "", "failed"))
        local_facts = LocalFactCollector().collect(module=module)
        assert "Failure executing" in local_facts["local"]["sample"]

        mock_output = """{"defaults": {"foo": "bar"}}"""
        mocker.patch.object(module, "run_command", return_value=(0, mock_output, ""))
        local_facts = LocalFactCollector().collect(module=module)
        assert local_facts["local"]["sample"]["defaults"]["foo"] == "bar"

        mock_config_output = "foo=bar\n"
        mocker.patch.object(
            module, "run_command", return_value=(0, mock_config_output, "")
        )
        local_facts = LocalFactCollector().collect(module=module)
        assert "error loading facts as JSON or ini" in local_facts["local"]["sample"]

        mock_config_output = "[defaults]\nfoo=bar\n"
        mocker.patch.object(
            module, "run_command", return_value=(0, mock_config_output, "")
        )
        local_facts = LocalFactCollector().collect(module=module)
        assert local_facts["local"]["sample"]["defaults"]["foo"] == "bar"

        mock_config_output = "[defaults]\n"
        mocker.patch.object(
            module, "run_command", return_value=(0, mock_config_output, "")
        )
        local_facts = LocalFactCollector().collect(module=module)
        assert local_facts["local"]["sample"]["defaults"] == {}

        mock_config_output = "[defaults]\n"
        mocker.patch.object(
            module, "run_command", return_value=(0, mock_config_output, "")
        )
        local_facts = LocalFactCollector().collect(module=module)
        assert local_facts["local"]["sample"]["defaults"] == {}

        mocker.patch.object(module, "run_command", return_value=(0, "", ""))
        mocker.patch(
            "json.loads", side_effect=Exception("fake _mock_json_load exception")
        )
        local_facts = LocalFactCollector().collect(module=module)
        assert (
            "Failed to convert (/usr/local/facts/sample.fact)"
            in local_facts["local"]["sample"]
        )

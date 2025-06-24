from __future__ import annotations

# test/units/playbook/test_playbook_include.py

from ansible.utils.collection_loader import _get_collection_name_from_path


def test_collection_playbook_path_detection():
    path = "/fake/path/collections/ansible_collections/my_namespace/my_collection/playbooks/site.yml"
    collection_name = _get_collection_name_from_path(path)
    assert collection_name == "my_namespace.my_collection"


def test_non_collection_playbook_path():
    path = "/home/aniket/playbooks/my_playbook.yml"
    collection_name = _get_collection_name_from_path(path)
    assert collection_name is None

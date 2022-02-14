import json
import tempfile
import textwrap

from ansible.galaxy import Galaxy
from ansible.cli.galaxy import GalaxyCLI, _marshall_role, _dump_roles
from ansible.module_utils.common.yaml import yaml_load

from .conftest import expected_roles_serialised


def test_dump_roles_yaml(found_roles):
    r = _dump_roles(found_roles, "yaml")
    deserialised = yaml_load(r)

    assert deserialised == expected_roles_serialised


def test_dump_roles_json(found_roles):
    r = _dump_roles(found_roles, "json")
    deserialised = json.loads(r)

    assert deserialised == expected_roles_serialised


def test_dump_roles_human(found_roles):
    r = _dump_roles(found_roles, "human")

    assert r == textwrap.dedent(
        """\
        # /root/.ansible/collections
        - sandwiches.pbj, 1.5.0
        - sandwiches.reuben, 2.5.0
        # /usr/share/ansible/collections
        - sandwiches.pbj, 1.0.0
        - sandwiches.ham, 1.0.0"""
    )


def test_dump_roles_requirements(found_roles, galaxy_server):
    result = _dump_roles(found_roles, "requirements")

    with tempfile.NamedTemporaryFile() as requirements_file:
        requirements_file.write(result.encode("utf-8"))
        requirements_file.flush()

        # mocking GalaxyCLI
        galaxy = GalaxyCLI(["--help"])  # any args, doesn't matter
        # needed for creating roles
        galaxy._api = galaxy_server
        galaxy.galaxy = Galaxy()

        deserialised = galaxy._parse_requirements_file(requirements_file.name)
        expected_roles = sum(found_roles.values(), [])

        assert len(deserialised["roles"]) == 4
        assert deserialised == {"collections": [], "roles": expected_roles}

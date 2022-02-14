import pytest

from ansible.galaxy import collection
from ansible.galaxy.dependency_resolution.dataclasses import Candidate, Requirement
from ansible.galaxy.role import GalaxyRole
from ansible import context
from ansible.galaxy import api, Galaxy


path_1 = "/root/.ansible/collections"
path_2 = "/usr/share/ansible/collections"


collections_path_1 = [
    Candidate("sandwiches.pbj", "1.5.0", None, "dir", None),
    Candidate("sandwiches.reuben", "2.5.0", None, "dir", None),
]
collections_path_2 = [
    Candidate("sandwiches.pbj", "1.0.0", None, "dir", None),
    Candidate("sandwiches.ham", "1.0.0", None, "dir", None),
]

found_collections = {path_1: collections_path_1, path_2: collections_path_2}


expected_collections_serialiased = {
    "/root/.ansible/collections": {
        "sandwiches.pbj": {"version": "1.5.0"},
        "sandwiches.reuben": {"version": "2.5.0"},
    },
    "/usr/share/ansible/collections": {
        "sandwiches.ham": {"version": "1.0.0"},
        "sandwiches.pbj": {"version": "1.0.0"},
    },
}


@pytest.fixture(autouse=True)
def galaxy_server():
    context.CLIARGS._store = {"ignore_certs": False, "type": "role"}
    galaxy_api = api.GalaxyAPI(None, "test_server", "https://galaxy.ansible.com")
    return galaxy_api


@pytest.fixture
def found_roles(galaxy_server):
    r1_0 = GalaxyRole(Galaxy(), galaxy_server, "sandwiches.pbj")
    r1_0._install_info = {"version": "1.5.0"}

    r1_1 = GalaxyRole(Galaxy(), galaxy_server, "sandwiches.reuben")
    r1_1._install_info = {"version": "2.5.0"}

    r2_0 = GalaxyRole(Galaxy(), galaxy_server, "sandwiches.pbj")
    r2_0._install_info = {"version": "1.0.0"}

    r2_1 = GalaxyRole(Galaxy(), galaxy_server, "sandwiches.ham")
    r2_1._install_info = {"version": "1.0.0"}

    return {path_1: [r1_0, r1_1], path_2: [r2_0, r2_1]}


# expected datastructure for listing roles in YAML or JSON format
expected_roles_serialised = {
    "/root/.ansible/collections": [
        {"name": "sandwiches.pbj", "version": "1.5.0"},
        {"name": "sandwiches.reuben", "version": "2.5.0"},
    ],
    "/usr/share/ansible/collections": [
        {"name": "sandwiches.pbj", "version": "1.0.0"},
        {"name": "sandwiches.ham", "version": "1.0.0"},
    ],
}


def cliargs(collections_paths=None, collection_name=None):
    if collections_paths is None:
        collections_paths = [
            "~/root/.ansible/collections",
            "/usr/share/ansible/collections",
        ]

    context.CLIARGS._store = {
        "collections_path": collections_paths,
        "collection": collection_name,
        "type": "collection",
        "output_format": "human",
    }

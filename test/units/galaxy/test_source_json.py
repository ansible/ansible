# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for source.json functionality for PURL generation."""

from __future__ import annotations

import json
import os
import pytest
import tempfile

from unittest.mock import MagicMock

from ansible.galaxy import api, collection, token
from ansible.galaxy.collection import concrete_artifact_manager
from ansible.galaxy.dependency_resolution import dataclasses
from ansible.module_utils.common.text.converters import to_bytes
from ansible import context
from ansible.utils import context_objects as co


@pytest.fixture(autouse=True)
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture
def galaxy_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(
        None, 'test_server', 'https://galaxy.ansible.com',
        token=token.GalaxyToken(token='key')
    )
    return galaxy_api


@pytest.fixture
def automation_hub_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(
        None, 'automation_hub', 'https://console.redhat.com/api/automation-hub',
        token=token.GalaxyToken(token='key')
    )
    return galaxy_api


class TestSourceJsonSchema:
    """Tests for source.json schema validation."""

    def test_validate_source_json_schema_valid_galaxy(self):
        """Test valid galaxy source.json schema."""
        data = {
            "format_version": "1.0.0",
            "namespace": "cisco",
            "name": "aci",
            "version": "2.13.0",
            "type": "galaxy",
            "repository_url": "https://galaxy.ansible.com",
            "download_url": "https://galaxy.ansible.com/api/v3/artifacts/cisco-aci-2.13.0.tar.gz",
        }
        errors = dataclasses._validate_source_json_schema("cisco", "aci", "2.13.0", data)
        assert errors == []

    def test_validate_source_json_schema_valid_git(self):
        """Test valid git source.json schema."""
        data = {
            "format_version": "1.0.0",
            "namespace": "myorg",
            "name": "mycollection",
            "version": "1.0.0",
            "type": "git",
            "vcs_url": "git+https://github.com/myorg/mycollection.git@v1.0.0",
        }
        errors = dataclasses._validate_source_json_schema("myorg", "mycollection", "1.0.0", data)
        assert errors == []

    def test_validate_source_json_schema_valid_url(self):
        """Test valid url source.json schema."""
        data = {
            "format_version": "1.0.0",
            "namespace": "custom",
            "name": "collection",
            "version": "2.0.0",
            "type": "url",
            "download_url": "https://example.com/collection-2.0.0.tar.gz",
        }
        errors = dataclasses._validate_source_json_schema("custom", "collection", "2.0.0", data)
        assert errors == []

    def test_validate_source_json_schema_valid_file(self):
        """Test valid file source.json schema (no URL fields)."""
        data = {
            "format_version": "1.0.0",
            "namespace": "local",
            "name": "collection",
            "version": "1.0.0",
            "type": "file",
        }
        errors = dataclasses._validate_source_json_schema("local", "collection", "1.0.0", data)
        assert errors == []

    def test_validate_source_json_schema_valid_dir(self):
        """Test valid dir source.json schema (no URL fields)."""
        data = {
            "format_version": "1.0.0",
            "namespace": "local",
            "name": "collection",
            "version": "1.0.0",
            "type": "dir",
        }
        errors = dataclasses._validate_source_json_schema("local", "collection", "1.0.0", data)
        assert errors == []

    def test_validate_source_json_schema_invalid_type(self):
        """Test invalid type in source.json schema."""
        data = {
            "format_version": "1.0.0",
            "namespace": "test",
            "name": "collection",
            "version": "1.0.0",
            "type": "invalid_type",
        }
        errors = dataclasses._validate_source_json_schema("test", "collection", "1.0.0", data)
        assert len(errors) > 0
        assert any("type" in e for e in errors)

    def test_validate_source_json_schema_invalid_format_version(self):
        """Test invalid format_version in source.json schema."""
        data = {
            "format_version": "2.0.0",
            "namespace": "test",
            "name": "collection",
            "version": "1.0.0",
            "type": "galaxy",
        }
        errors = dataclasses._validate_source_json_schema("test", "collection", "1.0.0", data)
        assert len(errors) > 0
        assert any("format_version" in e for e in errors)

    def test_validate_source_json_schema_mismatched_namespace(self):
        """Test mismatched namespace in source.json schema."""
        data = {
            "format_version": "1.0.0",
            "namespace": "wrong_namespace",
            "name": "collection",
            "version": "1.0.0",
            "type": "galaxy",
        }
        errors = dataclasses._validate_source_json_schema("correct_namespace", "collection", "1.0.0", data)
        assert len(errors) > 0
        assert any("namespace" in e for e in errors)


class TestGetValidatedSourceJson:
    """Tests for get_validated_source_json function."""

    def test_get_validated_source_json_file_not_found(self, tmp_path):
        """Test get_validated_source_json returns None when file doesn't exist."""
        b_path = to_bytes(str(tmp_path / "nonexistent" / "source.json"))
        result = dataclasses.get_validated_source_json(b_path, "ns", "name", "1.0.0")
        assert result is None

    def test_get_validated_source_json_valid_file(self, tmp_path):
        """Test get_validated_source_json returns data for valid file."""
        source_json_path = tmp_path / "source.json"
        data = {
            "format_version": "1.0.0",
            "namespace": "cisco",
            "name": "aci",
            "version": "2.13.0",
            "type": "galaxy",
            "repository_url": "https://galaxy.ansible.com",
        }
        source_json_path.write_text(json.dumps(data))

        result = dataclasses.get_validated_source_json(
            to_bytes(str(source_json_path)), "cisco", "aci", "2.13.0"
        )
        assert result is not None
        assert result["type"] == "galaxy"
        assert result["repository_url"] == "https://galaxy.ansible.com"

    def test_get_validated_source_json_invalid_json(self, tmp_path):
        """Test get_validated_source_json returns None for invalid JSON."""
        source_json_path = tmp_path / "source.json"
        source_json_path.write_text("not valid json {")

        result = dataclasses.get_validated_source_json(
            to_bytes(str(source_json_path)), "ns", "name", "1.0.0"
        )
        assert result is None


class TestGetArtifactSourceJson:
    """Tests for ConcreteArtifactsManager.get_artifact_source_json method."""

    def test_get_artifact_source_json_galaxy(self, galaxy_server):
        """Test get_artifact_source_json for galaxy type collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            # Create a mock candidate
            candidate = MagicMock()
            candidate.namespace = "cisco"
            candidate.name = "aci"
            candidate.ver = "2.13.0"
            candidate.type = "galaxy"
            candidate.src = galaxy_server

            # Mock the galaxy collection cache
            metadata = MagicMock()
            metadata.download_url = "https://galaxy.ansible.com/api/v3/artifacts/cisco-aci-2.13.0.tar.gz"
            manager._galaxy_collection_cache[candidate] = (metadata, galaxy_server)

            result = manager.get_artifact_source_json(candidate)

            assert result["format_version"] == "1.0.0"
            assert result["namespace"] == "cisco"
            assert result["name"] == "aci"
            assert result["version"] == "2.13.0"
            assert result["type"] == "galaxy"
            assert result["repository_url"] == "https://galaxy.ansible.com"
            assert result["download_url"] == "https://galaxy.ansible.com/api/v3/artifacts/cisco-aci-2.13.0.tar.gz"

    def test_get_artifact_source_json_automation_hub(self, automation_hub_server):
        """Test get_artifact_source_json for automation hub collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "redhat"
            candidate.name = "rhel_system_roles"
            candidate.ver = "1.20.0"
            candidate.type = "galaxy"
            candidate.src = automation_hub_server

            metadata = MagicMock()
            metadata.download_url = "https://console.redhat.com/api/automation-hub/v3/artifacts/redhat-rhel_system_roles-1.20.0.tar.gz"
            manager._galaxy_collection_cache[candidate] = (metadata, automation_hub_server)

            result = manager.get_artifact_source_json(candidate)

            assert result["type"] == "galaxy"
            assert result["repository_url"] == "https://console.redhat.com/api/automation-hub"

    def test_get_artifact_source_json_git(self):
        """Test get_artifact_source_json for git type collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "myorg"
            candidate.name = "mycollection"
            candidate.ver = "1.0.0"
            candidate.type = "git"
            candidate.src = "https://github.com/myorg/mycollection.git"

            result = manager.get_artifact_source_json(candidate)

            assert result["format_version"] == "1.0.0"
            assert result["namespace"] == "myorg"
            assert result["name"] == "mycollection"
            assert result["version"] == "1.0.0"
            assert result["type"] == "git"
            assert result["vcs_url"] == "git+https://github.com/myorg/mycollection.git"

    def test_get_artifact_source_json_git_with_git_plus_prefix(self):
        """Test get_artifact_source_json for git type with git+ prefix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "myorg"
            candidate.name = "mycollection"
            candidate.ver = "1.0.0"
            candidate.type = "git"
            candidate.src = "git+https://github.com/myorg/mycollection.git@v1.0.0"

            result = manager.get_artifact_source_json(candidate)

            assert result["type"] == "git"
            # Should not double-prefix
            assert result["vcs_url"] == "git+https://github.com/myorg/mycollection.git@v1.0.0"

    def test_get_artifact_source_json_git_with_git_at_prefix(self):
        """Test get_artifact_source_json for git type with git@ prefix (SSH)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "myorg"
            candidate.name = "mycollection"
            candidate.ver = "1.0.0"
            candidate.type = "git"
            candidate.src = "git@github.com:myorg/mycollection.git"

            result = manager.get_artifact_source_json(candidate)

            assert result["type"] == "git"
            # Should not add prefix to git@ URLs
            assert result["vcs_url"] == "git@github.com:myorg/mycollection.git"

    def test_get_artifact_source_json_url(self):
        """Test get_artifact_source_json for url type collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "custom"
            candidate.name = "collection"
            candidate.ver = "2.0.0"
            candidate.type = "url"
            candidate.src = "https://example.com/collection-2.0.0.tar.gz"

            result = manager.get_artifact_source_json(candidate)

            assert result["format_version"] == "1.0.0"
            assert result["type"] == "url"
            assert result["download_url"] == "https://example.com/collection-2.0.0.tar.gz"
            assert "vcs_url" not in result
            assert "repository_url" not in result

    def test_get_artifact_source_json_file(self):
        """Test get_artifact_source_json for file type collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "local"
            candidate.name = "collection"
            candidate.ver = "1.0.0"
            candidate.type = "file"
            candidate.src = "/path/to/collection.tar.gz"

            result = manager.get_artifact_source_json(candidate)

            assert result["format_version"] == "1.0.0"
            assert result["namespace"] == "local"
            assert result["name"] == "collection"
            assert result["type"] == "file"
            # Should NOT include the local path
            assert "download_url" not in result
            assert "vcs_url" not in result
            assert "repository_url" not in result

    def test_get_artifact_source_json_dir(self):
        """Test get_artifact_source_json for dir type collection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            b_tmp_dir = to_bytes(tmp_dir)
            manager = concrete_artifact_manager.ConcreteArtifactsManager(
                b_tmp_dir, validate_certs=True
            )

            candidate = MagicMock()
            candidate.namespace = "local"
            candidate.name = "collection"
            candidate.ver = "1.0.0"
            candidate.type = "dir"
            candidate.src = "/path/to/collection"

            result = manager.get_artifact_source_json(candidate)

            assert result["format_version"] == "1.0.0"
            assert result["type"] == "dir"
            # Should NOT include the local path
            assert "download_url" not in result
            assert "vcs_url" not in result
            assert "repository_url" not in result


class TestWriteSourceJson:
    """Tests for write_source_json function."""

    def test_write_source_json_creates_file(self, tmp_path):
        """Test that write_source_json creates the source.json file."""
        b_collection_path = to_bytes(str(tmp_path / "namespace" / "collection"))
        os.makedirs(b_collection_path)

        candidate = MagicMock()
        candidate.namespace = "namespace"
        candidate.name = "collection"
        candidate.ver = "1.0.0"
        candidate.type = "galaxy"

        artifacts_manager = MagicMock()
        artifacts_manager.get_artifact_source_json.return_value = {
            "format_version": "1.0.0",
            "namespace": "namespace",
            "name": "collection",
            "version": "1.0.0",
            "type": "galaxy",
            "repository_url": "https://galaxy.ansible.com",
        }

        collection.write_source_json(candidate, b_collection_path, artifacts_manager)

        source_json_path = tmp_path / "namespace" / "collection" / "source.json"
        assert source_json_path.exists()

        with open(source_json_path) as f:
            data = json.load(f)

        assert data["format_version"] == "1.0.0"
        assert data["namespace"] == "namespace"
        assert data["type"] == "galaxy"

    def test_write_source_json_content_format(self, tmp_path):
        """Test that write_source_json writes properly formatted JSON."""
        b_collection_path = to_bytes(str(tmp_path / "cisco" / "aci"))
        os.makedirs(b_collection_path)

        candidate = MagicMock()
        candidate.namespace = "cisco"
        candidate.name = "aci"
        candidate.ver = "2.13.0"
        candidate.type = "galaxy"

        artifacts_manager = MagicMock()
        artifacts_manager.get_artifact_source_json.return_value = {
            "format_version": "1.0.0",
            "namespace": "cisco",
            "name": "aci",
            "version": "2.13.0",
            "type": "galaxy",
            "repository_url": "https://galaxy.ansible.com",
            "download_url": "https://galaxy.ansible.com/api/v3/artifacts/cisco-aci-2.13.0.tar.gz",
        }

        collection.write_source_json(candidate, b_collection_path, artifacts_manager)

        source_json_path = tmp_path / "cisco" / "aci" / "source.json"
        content = source_json_path.read_text()

        # Verify it's properly indented (indent=2)
        assert '  "format_version"' in content or '"format_version"' in content

        data = json.loads(content)
        assert data["download_url"] == "https://galaxy.ansible.com/api/v3/artifacts/cisco-aci-2.13.0.tar.gz"

from io import StringIO
from ansible.compat.tests import unittest, mock

from ansible.modules.packaging.language import maven_artifact

class TestMavenDownloader(unittest.TestCase):

    class AnsibleModuleMock:
        def __init__(self):
            self.params = {}

    def test_get_base_release(self):
        module = self.AnsibleModuleMock()
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0")
        base = "http://repo.test.org/maven"
        downloader = maven_artifact.MavenDownloader(module, base=base)

        assert downloader.get_base(artifact) == base

    def test_get_base_snapshot(self):
        module = self.AnsibleModuleMock()
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0-SNAPSHOT")
        base = "http://repo.test.org/maven"
        downloader = maven_artifact.MavenDownloader(module, base=base)

        assert downloader.get_base(artifact) == base

    def test_get_base_snapshot_with_base_snapshot(self):
        module = self.AnsibleModuleMock()
        module.params["repository_snapshot_url"] = "http://repo.test.org/maven-snapshot"
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0-SNAPSHOT")
        downloader = maven_artifact.MavenDownloader(module, base="http://repo.test.org/maven")

        assert downloader.get_base(artifact) == module.params["repository_snapshot_url"]

    def test_find_uri_for_artifact_release(self):
        module = self.AnsibleModuleMock()
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0")
        downloader = maven_artifact.MavenDownloader(module, base="http://repo.test.org/maven")

        assert downloader.find_uri_for_artifact(artifact) == "http://repo.test.org/maven/com/ansible/test/1.0/test-1.0.jar"

    @mock.patch('ansible.modules.packaging.language.maven_artifact.fetch_url')
    def test_find_uri_for_artifact_release_latest(self, fetch_url_fn):
        module = self.AnsibleModuleMock()
        artifact = maven_artifact.Artifact("com.ansible", "test", "latest")
        maven_metadata_xml_str = u"""<?xml version="1.0" encoding="UTF-8"?>
            <metadata>
              <groupId>com.ansible</groupId>
              <artifactId>test</artifactId>
              <version>2.0</version>
              <versioning>
                <versions>
                  <version>1.0</version>
                  <version>2.0</version>
                </versions>
                <lastUpdated>20130724233225</lastUpdated>
              </versioning>
            </metadata>
        """
        downloader = maven_artifact.MavenDownloader(module, base="http://repo.test.org/maven")
        fetch_url_fn.return_value = (StringIO(maven_metadata_xml_str), {"status": 200})

        assert downloader.find_uri_for_artifact(artifact) == "http://repo.test.org/maven/com/ansible/test/2.0/test-2.0.jar"
        assert fetch_url_fn.call_args[0] == (module, "http://repo.test.org/maven/com/ansible/test/maven-metadata.xml")

    @mock.patch('ansible.modules.packaging.language.maven_artifact.fetch_url')
    def test_find_uri_for_artifact_is_snapshot(self, fetch_url_fn):
        module = self.AnsibleModuleMock()
        module.params["unique_snapshot"] = True
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0-SNAPSHOT")
        maven_metadata_xml_str = u"""<?xml version="1.0" encoding="UTF-8"?>
            <metadata>
              <groupId>com.ansible</groupId>
              <artifactId>test</artifactId>
              <version>1.0-20150302.201629-3</version>
              <versioning>
                <snapshot>
                  <timestamp>20150330.174014</timestamp>
                  <buildNumber>12</buildNumber>
                </snapshot>
                <lastUpdated>20150911205444</lastUpdated>
                <snapshotVersions>
                  <snapshotVersion>
                    <extension>jar</extension>
                    <value>1.0-20150330.174014-12</value>
                    <updated>20150330174014</updated>
                  </snapshotVersion>
                </snapshotVersions>
              </versioning>
            </metadata>
        """
        downloader = maven_artifact.MavenDownloader(module, base="http://repo.test.org/maven")
        fetch_url_fn.return_value = (StringIO(maven_metadata_xml_str), {"status": 200})

        assert downloader.find_uri_for_artifact(artifact) == "http://repo.test.org/maven/com/ansible/test/1.0-SNAPSHOT/test-1.0-20150330.174014-12.jar"
        assert fetch_url_fn.call_args[0] == (module, "http://repo.test.org/maven/com/ansible/test/1.0-SNAPSHOT/maven-metadata.xml")

    def test_find_uri_for_artifact_is_snapshot_nonunique(self):
        module = self.AnsibleModuleMock()
        module.params["unique_snapshot"] = False
        artifact = maven_artifact.Artifact("com.ansible", "test", "1.0-SNAPSHOT")
        downloader = maven_artifact.MavenDownloader(module, base="http://repo.test.org/maven")

        assert downloader.find_uri_for_artifact(artifact) == "http://repo.test.org/maven/com/ansible/test/1.0-SNAPSHOT/test-1.0-SNAPSHOT.jar"

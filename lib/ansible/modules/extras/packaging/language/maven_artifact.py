#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, Chris Schmidt <chris.schmidt () contrastsecurity.com>
#
# Built using https://github.com/hamnis/useful-scripts/blob/master/python/download-maven-artifact
# as a reference and starting point.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'cschmidt'

from lxml import etree
import os
import hashlib
import sys
import posixpath
import urlparse
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

DOCUMENTATION = '''
---
module: maven_artifact
short_description: Downloads an Artifact from a Maven Repository
version_added: "2.0"
description:
    - Downloads an artifact from a maven repository given the maven coordinates provided to the module. Can retrieve
    - snapshots or release versions of the artifact and will resolve the latest available version if one is not
    - available.
author: "Chris Schmidt (@chrisisbeef)"
requirements:
    - "python >= 2.6"
    - lxml
    - boto if using a S3 repository (s3://...)
options:
    group_id:
        description:
            - The Maven groupId coordinate
        required: true
    artifact_id:
        description:
            - The maven artifactId coordinate
        required: true
    version:
        description:
            - The maven version coordinate
        required: false
        default: latest
    classifier:
        description:
            - The maven classifier coordinate
        required: false
        default: null
    extension:
        description:
            - The maven type/extension coordinate
        required: false
        default: jar
    repository_url:
        description:
            - The URL of the Maven Repository to download from.
            - Use s3://... if the repository is hosted on Amazon S3, added in version 2.2.
        required: false
        default: http://repo1.maven.org/maven2
    username:
        description:
            - The username to authenticate as to the Maven Repository. Use AWS secret key of the repository is hosted on S3
        required: false
        default: null
        aliases: [ "aws_secret_key" ]
    password:
        description:
            - The password to authenticate with to the Maven Repository. Use AWS secret access key of the repository is hosted on S3
        required: false
        default: null
        aliases: [ "aws_secret_access_key" ]
    dest:
        description:
            - The path where the artifact should be written to
        required: true
        default: false
    state:
        description:
            - The desired state of the artifact
        required: true
        default: present
        choices: [present,absent]
    timeout:
        description:
            - Specifies a timeout in seconds for the connection attempt
        required: false
        default: 10
        version_added: "2.3"
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be set to C(no) when no other option exists.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: "1.9.3"
'''

EXAMPLES = '''
# Download the latest version of the JUnit framework artifact from Maven Central
- maven_artifact: group_id=junit artifact_id=junit dest=/tmp/junit-latest.jar

# Download JUnit 4.11 from Maven Central
- maven_artifact: group_id=junit artifact_id=junit version=4.11 dest=/tmp/junit-4.11.jar

# Download an artifact from a private repository requiring authentication
- maven_artifact: group_id=com.company artifact_id=library-name repository_url=https://repo.company.com/maven username=user password=pass dest=/tmp/library-name-latest.jar

# Download a WAR File to the Tomcat webapps directory to be deployed
- maven_artifact: group_id=com.company artifact_id=web-app extension=war repository_url=https://repo.company.com/maven dest=/var/lib/tomcat7/webapps/web-app.war
'''

class Artifact(object):
    def __init__(self, group_id, artifact_id, version, classifier=None, extension='jar'):
        if not group_id:
            raise ValueError("group_id must be set")
        if not artifact_id:
            raise ValueError("artifact_id must be set")

        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version
        self.classifier = classifier

        if not extension:
            self.extension = "jar"
        else:
            self.extension = extension

    def is_snapshot(self):
        return self.version and self.version.endswith("SNAPSHOT")

    def path(self, with_version=True):
        base = posixpath.join(self.group_id.replace(".", "/"), self.artifact_id)
        if with_version and self.version:
            return posixpath.join(base, self.version)
        else:
            return base

    def _generate_filename(self):
        if not self.classifier:
            return self.artifact_id + "." + self.extension
        else:
            return self.artifact_id + "-" + self.classifier + "." + self.extension

    def get_filename(self, filename=None):
        if not filename:
            filename = self._generate_filename()
        elif os.path.isdir(filename):
            filename = os.path.join(filename, self._generate_filename())
        return filename

    def __str__(self):
        if self.classifier:
            return "%s:%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.classifier, self.version)
        elif self.extension != "jar":
            return "%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.version)
        else:
            return "%s:%s:%s" % (self.group_id, self.artifact_id, self.version)

    @staticmethod
    def parse(input):
        parts = input.split(":")
        if len(parts) >= 3:
            g = parts[0]
            a = parts[1]
            v = parts[len(parts) - 1]
            t = None
            c = None
            if len(parts) == 4:
                t = parts[2]
            if len(parts) == 5:
                t = parts[2]
                c = parts[3]
            return Artifact(g, a, v, c, t)
        else:
            return None


class MavenDownloader:
    def __init__(self, module, base="http://repo1.maven.org/maven2"):
        self.module = module
        if base.endswith("/"):
            base = base.rstrip("/")
        self.base = base
        self.user_agent = "Maven Artifact Downloader/1.0"

    def _find_latest_version_available(self, artifact):
        path = "/%s/maven-metadata.xml" % (artifact.path(False))
        xml = self._request(self.base + path, "Failed to download maven-metadata.xml", lambda r: etree.parse(r))
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            return v[0]

    def find_uri_for_artifact(self, artifact):
        if artifact.version == "latest":
            artifact.version = self._find_latest_version_available(artifact)

        if artifact.is_snapshot():
            path = "/%s/maven-metadata.xml" % (artifact.path())
            xml = self._request(self.base + path, "Failed to download maven-metadata.xml", lambda r: etree.parse(r))
            timestamp = xml.xpath("/metadata/versioning/snapshot/timestamp/text()")[0]
            buildNumber = xml.xpath("/metadata/versioning/snapshot/buildNumber/text()")[0]
            for snapshotArtifact in xml.xpath("/metadata/versioning/snapshotVersions/snapshotVersion"):
                if len(snapshotArtifact.xpath("classifier/text()")) > 0 and snapshotArtifact.xpath("classifier/text()")[0] == artifact.classifier and len(snapshotArtifact.xpath("extension/text()")) > 0 and snapshotArtifact.xpath("extension/text()")[0] == artifact.extension:
                    return self._uri_for_artifact(artifact, snapshotArtifact.xpath("value/text()")[0])
            return self._uri_for_artifact(artifact, artifact.version.replace("SNAPSHOT", timestamp + "-" + buildNumber))

        return self._uri_for_artifact(artifact, artifact.version)

    def _uri_for_artifact(self, artifact, version=None):
        if artifact.is_snapshot() and not version:
            raise ValueError("Expected uniqueversion for snapshot artifact " + str(artifact))
        elif not artifact.is_snapshot():
            version = artifact.version
        if artifact.classifier:
            return posixpath.join(self.base, artifact.path(), artifact.artifact_id + "-" + version + "-" + artifact.classifier + "." + artifact.extension)

        return posixpath.join(self.base, artifact.path(), artifact.artifact_id + "-" + version + "." + artifact.extension)

    def _request(self, url, failmsg, f):
        url_to_use = url
        parsed_url = urlparse(url)
        if parsed_url.scheme=='s3':
                parsed_url = urlparse(url)
                bucket_name = parsed_url.netloc
                key_name = parsed_url.path[1:]
                client = boto3.client('s3',aws_access_key_id=self.module.params.get('username', ''), aws_secret_access_key=self.module.params.get('password', ''))
                url_to_use = client.generate_presigned_url('get_object',Params={'Bucket':bucket_name,'Key':key_name},ExpiresIn=10)

        req_timeout = self.module.params.get('timeout')

        # Hack to add parameters in the way that fetch_url expects
        self.module.params['url_username'] = self.module.params.get('username', '')
        self.module.params['url_password'] = self.module.params.get('password', '')
        self.module.params['http_agent'] = self.module.params.get('user_agent', None)

        response, info = fetch_url(self.module, url_to_use, timeout=req_timeout)
        if info['status'] != 200:
            raise ValueError(failmsg + " because of " + info['msg'] + "for URL " + url_to_use)
        else:
            return f(response)


    def download(self, artifact, filename=None):
        filename = artifact.get_filename(filename)
        if not artifact.version or artifact.version == "latest":
            artifact = Artifact(artifact.group_id, artifact.artifact_id, self._find_latest_version_available(artifact),
                                artifact.classifier, artifact.extension)

        url = self.find_uri_for_artifact(artifact)
        if not self.verify_md5(filename, url + ".md5"):
            response = self._request(url, "Failed to download artifact " + str(artifact), lambda r: r)
            if response:
                f = open(filename, 'w')
                # f.write(response.read())
                self._write_chunks(response, f, report_hook=self.chunk_report)
                f.close()
                return True
            else:
                return False
        else:
            return True

    def chunk_report(self, bytes_so_far, chunk_size, total_size):
        percent = float(bytes_so_far) / total_size
        percent = round(percent * 100, 2)
        sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" %
                         (bytes_so_far, total_size, percent))

        if bytes_so_far >= total_size:
            sys.stdout.write('\n')

    def _write_chunks(self, response, file, chunk_size=8192, report_hook=None):
        total_size = response.info().getheader('Content-Length').strip()
        total_size = int(total_size)
        bytes_so_far = 0

        while 1:
            chunk = response.read(chunk_size)
            bytes_so_far += len(chunk)

            if not chunk:
                break

            file.write(chunk)
            if report_hook:
                report_hook(bytes_so_far, chunk_size, total_size)

        return bytes_so_far

    def verify_md5(self, file, remote_md5):
        if not os.path.exists(file):
            return False
        else:
            local_md5 = self._local_md5(file)
            remote = self._request(remote_md5, "Failed to download MD5", lambda r: r.read())
            return local_md5 == remote

    def _local_md5(self, file):
        md5 = hashlib.md5()
        f = open(file, 'rb')
        for chunk in iter(lambda: f.read(8192), ''):
            md5.update(chunk)
        f.close()
        return md5.hexdigest()


def main():
    module = AnsibleModule(
        argument_spec = dict(
            group_id = dict(default=None),
            artifact_id = dict(default=None),
            version = dict(default="latest"),
            classifier = dict(default=None),
            extension = dict(default='jar'),
            repository_url = dict(default=None),
            username = dict(default=None,aliases=['aws_secret_key']),
            password = dict(default=None, no_log=True,aliases=['aws_secret_access_key']),
            state = dict(default="present", choices=["present","absent"]), # TODO - Implement a "latest" state
            timeout = dict(default=10, type='int'),
            dest = dict(type="path", default=None),
            validate_certs = dict(required=False, default=True, type='bool'),
        )
    )

    try:
        parsed_url = urlparse(module.params["repository_url"])
    except AttributeError as e:
        module.fail_json(msg='url parsing went wrong %s' % e)

    if parsed_url.scheme=='s3' and not HAS_BOTO:
        module.fail_json(msg='boto3 required for this module, when using s3:// repository URLs')

    group_id = module.params["group_id"]
    artifact_id = module.params["artifact_id"]
    version = module.params["version"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    repository_url = module.params["repository_url"]
    repository_username = module.params["username"]
    repository_password = module.params["password"]
    state = module.params["state"]
    dest = module.params["dest"]

    if not repository_url:
        repository_url = "http://repo1.maven.org/maven2"

    #downloader = MavenDownloader(module, repository_url, repository_username, repository_password)
    downloader = MavenDownloader(module, repository_url)

    try:
        artifact = Artifact(group_id, artifact_id, version, classifier, extension)
    except ValueError as e:
        module.fail_json(msg=e.args[0])

    prev_state = "absent"
    if os.path.isdir(dest):
        dest = posixpath.join(dest, artifact_id + "-" + version + "." + extension)
    if os.path.lexists(dest) and downloader.verify_md5(dest, downloader.find_uri_for_artifact(artifact) + '.md5'):
        prev_state = "present"
    else:
        path = os.path.dirname(dest)
        if not os.path.exists(path):
            os.makedirs(path)

    if prev_state == "present":
        module.exit_json(dest=dest, state=state, changed=False)

    try:
        if downloader.download(artifact, dest):
            module.exit_json(state=state, dest=dest, group_id=group_id, artifact_id=artifact_id, version=version, classifier=classifier, extension=extension, repository_url=repository_url, changed=True)
        else:
            module.fail_json(msg="Unable to download the artifact")
    except ValueError as e:
        module.fail_json(msg=e.args[0])



if __name__ == '__main__':
    main()

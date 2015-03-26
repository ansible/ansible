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
from urllib2 import Request, urlopen, URLError, HTTPError
import os
import hashlib
import sys
import base64

DOCUMENTATION = '''
---
module: maven_artifact
short_description: Downloads an Artifact from a Maven Repository
version_added: "2.0"
description:
    - Downloads an artifact from a maven repository given the maven coordinates provided to the module. Can retrieve
    - snapshots or release versions of the artifact and will resolve the latest available version if one is not
    - available.
author: Chris Schmidt <chris.schmidt () contrastsecurity.com>
requirements:
    - python libxml
    - python urllib2
options:
    group_id:
        description: The Maven groupId coordinate
        required: true
    artifact_id:
        description: The maven artifactId coordinate
        required: true
    version:
        description: The maven version coordinate
        required: false
        default: latest
    classifier:
        description: The maven classifier coordinate
        required: false
        default: null
    extension:
        description: The maven type/extension coordinate
        required: false
        default: jar
    repository_url:
        description: The URL of the Maven Repository to download from
        required: false
        default: http://repo1.maven.org/maven2
    username:
        description: The username to authenticate as to the Maven Repository
        required: false
        default: null
    password:
        description: The passwor to authenticate with to the Maven Repository
        required: false
        default: null
    dest:
        description: The path where the artifact should be written to
        required: true
        default: false
    state:
        description: The desired state of the artifact
        required: true
        default: present
        choices: [present,absent]
'''

EXAMPLES = '''
# Download the latest version of the commons-collections artifact from Maven Central
- maven_artifact: group_id=org.apache.commons artifact_id=commons-collections dest=/tmp/commons-collections-latest.jar

# Download Apache Commons-Collections 3.2 from Maven Central
- maven_artifact: group_id=org.apache.commons artifact_id=commons-collections version=3.2 dest=/tmp/commons-collections-3.2.jar

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
        base = self.group_id.replace(".", "/") + "/" + self.artifact_id
        if with_version and self.version:
            return base + "/" + self.version
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
    def __init__(self, base="http://repo1.maven.org/maven2", username=None, password=None):
        if base.endswith("/"):
            base = base.rstrip("/")
        self.base = base
        self.user_agent = "Maven Artifact Downloader/1.0"
        self.username = username
        self.password = password

    def _find_latest_version_available(self, artifact):
        path = "/%s/maven-metadata.xml" % (artifact.path(False))
        xml = self._request(self.base + path, "Failed to download maven-metadata.xml", lambda r: etree.parse(r))
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            return v[0]

    def find_uri_for_artifact(self, artifact):
        if artifact.is_snapshot():
            path = "/%s/maven-metadata.xml" % (artifact.path())
            xml = self._request(self.base + path, "Failed to download maven-metadata.xml", lambda r: etree.parse(r))
            basexpath = "/metadata/versioning/"
            p = xml.xpath(basexpath + "/snapshotVersions/snapshotVersion")
            if p:
                return self._find_matching_artifact(p, artifact)
        else:
            return self._uri_for_artifact(artifact)

    def _find_matching_artifact(self, elems, artifact):
        filtered = filter(lambda e: e.xpath("extension/text() = '%s'" % artifact.extension), elems)
        if artifact.classifier:
            filtered = filter(lambda e: e.xpath("classifier/text() = '%s'" % artifact.classifier), elems)

        if len(filtered) > 1:
            print(
                "There was more than one match. Selecting the first one. Try adding a classifier to get a better match.")
        elif not len(filtered):
            print("There were no matches.")
            return None

        elem = filtered[0]
        value = elem.xpath("value/text()")
        return self._uri_for_artifact(artifact, value[0])

    def _uri_for_artifact(self, artifact, version=None):
        if artifact.is_snapshot() and not version:
            raise ValueError("Expected uniqueversion for snapshot artifact " + str(artifact))
        elif not artifact.is_snapshot():
            version = artifact.version
        if artifact.classifier:
            return self.base + "/" + artifact.path() + "/" + artifact.artifact_id + "-" + version + "-" + artifact.classifier + "." + artifact.extension

        return self.base + "/" + artifact.path() + "/" + artifact.artifact_id + "-" + version + "." + artifact.extension

    def _request(self, url, failmsg, f):
        if not self.username:
            headers = {"User-Agent": self.user_agent}
        else:
            headers = {
                "User-Agent": self.user_agent,
                "Authorization": "Basic " + base64.b64encode(self.username + ":" + self.password)
            }
        req = Request(url, None, headers)
        try:
            response = urlopen(req)
        except HTTPError, e:
            raise ValueError(failmsg + " because of " + str(e) + "for URL " + url)
        except URLError, e:
            raise ValueError(failmsg + " because of " + str(e) + "for URL " + url)
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
                with open(filename, 'w') as f:
                    # f.write(response.read())
                    self._write_chunks(response, f, report_hook=self.chunk_report)
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
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), ''):
                md5.update(chunk)
        return md5.hexdigest()


def main():
    module = AnsibleModule(
        argument_spec = dict(
            group_id = dict(default=None),
            artifact_id = dict(default=None),
            version = dict(default=None),
            classifier = dict(default=None),
            extension = dict(default=None),
            repository_url = dict(default=None),
            username = dict(default=None),
            password = dict(default=None),
            state = dict(default="present", choices=["present","absent"]), # TODO - Implement a "latest" state 
            dest = dict(default=None),
        )
    )

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

    downloader = MavenDownloader(repository_url, repository_username, repository_password)

    try:
        artifact = Artifact(group_id, artifact_id, version, classifier, extension)
    except ValueError as e:
        module.fail_json(msg=e.args[0])

    prev_state = "absent"
    if os.path.isdir(dest):
        dest = dest + "/" + artifact_id + "-" + version + "." + extension
    if os.path.lexists(dest):
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


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, Chris Schmidt <chris.schmidt () contrastsecurity.com>
#
# Built using https://github.com/hamnis/useful-scripts/blob/master/python/download-maven-artifact
# as a reference and starting point.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: maven_artifact
short_description: Downloads an Artifact from a Maven Repository
version_added: "2.0"
description:
    - Downloads an artifact from a maven repository given the maven coordinates provided to the module.
    - Can retrieve snapshots or release versions of the artifact and will resolve the latest available
      version if one is not available.
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
            - If file mode or ownerships are specified and destination path already exists, they affect the downloaded file
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
    keep_name:
        description:
            - If C(yes), the downloaded artifact's name is preserved, i.e the version number remains part of it.
            - This option only has effect when C(dest) is a directory and C(version) is set to C(latest).
        required: false
        default: 'no'
        choices: ['yes', 'no']
        version_added: "2.4"
    force:
        description:
            - The default is C(yes), which will replace the remote file when its md5 sum is different than the md5 file downloaded from the repository.
              This may fail with some repositories if the md5 has not been computed;
              or if it acts as a proxy/cache and the artifact has not been cached yet.
            - If no, the artifact will only be transferred if the destination does not exist.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: "2.5"
extends_documentation_fragment:
    - files
'''

EXAMPLES = '''
# Download the latest version of the JUnit framework artifact from Maven Central
- maven_artifact:
    group_id: junit
    artifact_id: junit
    dest: /tmp/junit-latest.jar

# Download JUnit 4.11 from Maven Central
- maven_artifact:
    group_id: junit
    artifact_id: junit
    version: 4.11
    dest: /tmp/junit-4.11.jar

# Download an artifact from a private repository requiring authentication
- maven_artifact:
    group_id: com.company
    artifact_id: library-name
    repository_url: 'https://repo.company.com/maven'
    username: user
    password: pass
    dest: /tmp/library-name-latest.jar

# Download a WAR File to the Tomcat webapps directory to be deployed
- maven_artifact:
    group_id: com.company
    artifact_id: web-app
    extension: war
    repository_url: 'https://repo.company.com/maven'
    dest: /var/lib/tomcat7/webapps/web-app.war

# Keep a downloaded artifact's name, i.e. retain the version
- maven_artifact:
    version: latest
    artifact_id: spring-core
    group_id: org.springframework
    dest: /tmp/
    keep_name: yes
'''

import hashlib
import os
import posixpath
import sys

from lxml import etree

try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes


def split_pre_existing_dir(dirname):
    '''
    Return the first pre-existing directory and a list of the new directories that will be created.
    '''

    head, tail = os.path.split(dirname)
    b_head = to_bytes(head, errors='surrogate_or_strict')
    if not os.path.exists(b_head):
        (pre_existing_dir, new_directory_list) = split_pre_existing_dir(head)
    else:
        return head, [tail]
    new_directory_list.append(tail)
    return pre_existing_dir, new_directory_list


def adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed):
    '''
    Walk the new directories list and make sure that permissions are as we would expect
    '''

    if new_directory_list:
        working_dir = os.path.join(pre_existing_dir, new_directory_list.pop(0))
        directory_args['path'] = working_dir
        changed = module.set_fs_attributes_if_different(directory_args, changed)
        changed = adjust_recursive_directory_permissions(working_dir, new_directory_list, module, directory_args, changed)
    return changed


class Artifact(object):
    def __init__(self, group_id, artifact_id, version, classifier='', extension='jar'):
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
            base = posixpath.join(base, self.version)
        return base

    def _generate_filename(self):
        filename = self.artifact_id + "-" + self.classifier + "." + self.extension
        if not self.classifier:
            filename = self.artifact_id + "." + self.extension
        return filename

    def get_filename(self, filename=None):
        if not filename:
            filename = self._generate_filename()
        elif os.path.isdir(filename):
            filename = os.path.join(filename, self._generate_filename())
        return filename

    def __str__(self):
        result = "%s:%s:%s" % (self.group_id, self.artifact_id, self.version)
        if self.classifier:
            result = "%s:%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.classifier, self.version)
        elif self.extension != "jar":
            result = "%s:%s:%s:%s" % (self.group_id, self.artifact_id, self.extension, self.version)
        return result

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
        self.latest_version_found = None

    def find_latest_version_available(self, artifact):
        if self.latest_version_found:
            return self.latest_version_found
        path = "/%s/maven-metadata.xml" % (artifact.path(False))
        xml = self._request(self.base + path, "Failed to download maven-metadata.xml", etree.parse)
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            self.latest_version_found = v[0]
            return v[0]

    def find_uri_for_artifact(self, artifact):
        if artifact.version == "latest":
            artifact.version = self.find_latest_version_available(artifact)

        if artifact.is_snapshot():
            path = "/%s/maven-metadata.xml" % (artifact.path())
            xml = self._request(self.base + path, "Failed to download maven-metadata.xml", etree.parse)
            timestamp = xml.xpath("/metadata/versioning/snapshot/timestamp/text()")[0]
            buildNumber = xml.xpath("/metadata/versioning/snapshot/buildNumber/text()")[0]
            for snapshotArtifact in xml.xpath("/metadata/versioning/snapshotVersions/snapshotVersion"):
                classifier = snapshotArtifact.xpath("classifier/text()")
                artifact_classifier = classifier[0] if classifier else ''
                extension = snapshotArtifact.xpath("extension/text()")
                artifact_extension = extension[0] if extension else ''
                if artifact_classifier == artifact.classifier and artifact_extension == artifact.extension:
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
            artifact = Artifact(artifact.group_id, artifact.artifact_id, self.find_latest_version_available(artifact),
                                artifact.classifier, artifact.extension)

        url = self.find_uri_for_artifact(artifact)
        result = True
        if not self.verify_md5(filename, url + ".md5"):
            response = self._request(url, "Failed to download artifact " + str(artifact), lambda r: r)
            if response:
                f = open(filename, 'w')
                # f.write(response.read())
                self._write_chunks(response, f, report_hook=self.chunk_report)
                f.close()
            else:
                result = False
        return result

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
        result = False
        if os.path.exists(file):
            local_md5 = self._local_md5(file)
            remote = self._request(remote_md5, "Failed to download MD5", lambda r: r.read())
            result = local_md5 == remote
        return result

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
            classifier = dict(default=''),
            extension = dict(default='jar'),
            repository_url = dict(default=None),
            username = dict(default=None,aliases=['aws_secret_key']),
            password = dict(default=None, no_log=True,aliases=['aws_secret_access_key']),
            state = dict(default="present", choices=["present","absent"]), # TODO - Implement a "latest" state
            timeout = dict(default=10, type='int'),
            dest = dict(type="path", default=None),
            validate_certs = dict(required=False, default=True, type='bool'),
            keep_name = dict(required=False, default=False, type='bool'),
            force = dict(required=False, default=True, type='bool'),
        ),
        add_file_common_args=True
    )

    repository_url = module.params["repository_url"]
    if not repository_url:
        repository_url = "http://repo1.maven.org/maven2"

    try:
        parsed_url = urlparse(repository_url)
    except AttributeError as e:
        module.fail_json(msg='url parsing went wrong %s' % e)

    if parsed_url.scheme=='s3' and not HAS_BOTO:
        module.fail_json(msg='boto3 required for this module, when using s3:// repository URLs')

    group_id = module.params["group_id"]
    artifact_id = module.params["artifact_id"]
    version = module.params["version"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    state = module.params["state"]
    dest = module.params["dest"]
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    keep_name = module.params["keep_name"]
    force = module.params["force"]

    #downloader = MavenDownloader(module, repository_url, repository_username, repository_password)
    downloader = MavenDownloader(module, repository_url)

    try:
        artifact = Artifact(group_id, artifact_id, version, classifier, extension)
    except ValueError as e:
        module.fail_json(msg=e.args[0])

    changed = False
    prev_state = "absent"

    if dest.endswith(os.sep):
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        if not os.path.exists(b_dest):
            (pre_existing_dir, new_directory_list) = split_pre_existing_dir(dest)
            os.makedirs(b_dest)
            directory_args = module.load_file_common_arguments(module.params)
            directory_mode = module.params["directory_mode"]
            if directory_mode is not None:
                directory_args['mode'] = directory_mode
            else:
                directory_args['mode'] = None
            changed = adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed)

    if os.path.isdir(b_dest):
        version_part = version
        if keep_name and version == 'latest':
            version_part = downloader.find_latest_version_available(artifact)

        if classifier:
            dest = posixpath.join(dest, "%s-%s-%s.%s" % (artifact_id, version_part, classifier, extension))
        else:
            dest = posixpath.join(dest, "%s-%s.%s" % (artifact_id, version_part, extension))
        b_dest = to_bytes(dest, errors='surrogate_or_strict')

    if os.path.lexists(b_dest) and ((not force) or downloader.verify_md5(dest, downloader.find_uri_for_artifact(artifact) + '.md5')):
        prev_state = "present"

    if prev_state == "absent":
        try:
            if downloader.download(artifact, b_dest):
                changed = True
            else:
                module.fail_json(msg="Unable to download the artifact")
        except ValueError as e:
            module.fail_json(msg=e.args[0])

    module.params['dest'] = dest
    file_args = module.load_file_common_arguments(module.params)
    changed = module.set_fs_attributes_if_different(file_args, changed)
    if changed:
        module.exit_json(state=state, dest=dest, group_id=group_id, artifact_id=artifact_id, version=version, classifier=classifier,
                         extension=extension, repository_url=repository_url, changed=changed)
    else:
        module.exit_json(state=state, dest=dest, changed=changed)


if __name__ == '__main__':
    main()

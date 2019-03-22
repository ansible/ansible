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
        default: latest
    classifier:
        description:
            - The maven classifier coordinate
    extension:
        description:
            - The maven type/extension coordinate
        default: jar
    repository_url:
        description:
            - The URL of the Maven Repository to download from.
            - Use s3://... if the repository is hosted on Amazon S3, added in version 2.2.
            - Use file://... if the repository is local, added in version 2.6
        default: http://repo1.maven.org/maven2
    username:
        description:
            - The username to authenticate as to the Maven Repository. Use AWS secret key of the repository is hosted on S3
        aliases: [ "aws_secret_key" ]
    password:
        description:
            - The password to authenticate with to the Maven Repository. Use AWS secret access key of the repository is hosted on S3
        aliases: [ "aws_secret_access_key" ]
    headers:
        description:
            - Add custom HTTP headers to a request in hash/dict format.
        type: dict
        version_added: "2.8"
    dest:
        description:
            - The path where the artifact should be written to
            - If file mode or ownerships are specified and destination path already exists, they affect the downloaded file
        required: true
    state:
        description:
            - The desired state of the artifact
        default: present
        choices: [present,absent]
    timeout:
        description:
            - Specifies a timeout in seconds for the connection attempt
        default: 10
        version_added: "2.3"
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be set to C(no) when no other option exists.
        type: bool
        default: 'yes'
        version_added: "1.9.3"
    keep_name:
        description:
            - If C(yes), the downloaded artifact's name is preserved, i.e the version number remains part of it.
            - This option only has effect when C(dest) is a directory and C(version) is set to C(latest).
        type: bool
        default: 'no'
        version_added: "2.4"
    verify_checksum:
        description:
            - If C(never), the md5 checksum will never be downloaded and verified.
            - If C(download), the md5 checksum will be downloaded and verified only after artifact download. This is the default.
            - If C(change), the md5 checksum will be downloaded and verified if the destination already exist,
              to verify if they are identical. This was the behaviour before 2.6. Since it downloads the md5 before (maybe)
              downloading the artifact, and since some repository software, when acting as a proxy/cache, return a 404 error
              if the artifact has not been cached yet, it may fail unexpectedly.
              If you still need it, you should consider using C(always) instead - if you deal with a checksum, it is better to
              use it to verify integrity after download.
            - C(always) combines C(download) and C(change).
        required: false
        default: 'download'
        choices: ['never', 'download', 'change', 'always']
        version_added: "2.6"
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

# Download the latest version of the JUnit framework artifact from Maven local
- maven_artifact:
    group_id: junit
    artifact_id: junit
    dest: /tmp/junit-latest.jar
    repository_url: "file://{{ lookup('env','HOME') }}/.m2/repository"
'''

import hashlib
import os
import posixpath
import shutil
import io
import tempfile
import traceback

LXML_ETREE_IMP_ERR = None
try:
    from lxml import etree
    HAS_LXML_ETREE = True
except ImportError:
    LXML_ETREE_IMP_ERR = traceback.format_exc()
    HAS_LXML_ETREE = False

BOTO_IMP_ERR = None
try:
    import boto3
    HAS_BOTO = True
except ImportError:
    BOTO_IMP_ERR = traceback.format_exc()
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes, to_native, to_text


def split_pre_existing_dir(dirname):
    '''
    Return the first pre-existing directory and a list of the new directories that will be created.
    '''
    head, tail = os.path.split(dirname)
    b_head = to_bytes(head, errors='surrogate_or_strict')
    if not os.path.exists(b_head):
        if head == dirname:
            return None, [head]
        else:
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
        first_sub_dir = new_directory_list.pop(0)
        if not pre_existing_dir:
            working_dir = first_sub_dir
        else:
            working_dir = os.path.join(pre_existing_dir, first_sub_dir)
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
    def __init__(self, module, base="http://repo1.maven.org/maven2", local=False, headers=None):
        self.module = module
        if base.endswith("/"):
            base = base.rstrip("/")
        self.base = base
        self.local = local
        self.headers = headers
        self.user_agent = "Maven Artifact Downloader/1.0"
        self.latest_version_found = None
        self.metadata_file_name = "maven-metadata-local.xml" if local else "maven-metadata.xml"

    def find_latest_version_available(self, artifact):
        if self.latest_version_found:
            return self.latest_version_found
        path = "/%s/%s" % (artifact.path(False), self.metadata_file_name)
        content = self._getContent(self.base + path, "Failed to retrieve the maven metadata file: " + path)
        xml = etree.fromstring(content)
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            self.latest_version_found = v[0]
            return v[0]

    def find_uri_for_artifact(self, artifact):
        if artifact.version == "latest":
            artifact.version = self.find_latest_version_available(artifact)

        if artifact.is_snapshot():
            if self.local:
                return self._uri_for_artifact(artifact, artifact.version)
            path = "/%s/%s" % (artifact.path(), self.metadata_file_name)
            content = self._getContent(self.base + path, "Failed to retrieve the maven metadata file: " + path)
            xml = etree.fromstring(content)

            for snapshotArtifact in xml.xpath("/metadata/versioning/snapshotVersions/snapshotVersion"):
                classifier = snapshotArtifact.xpath("classifier/text()")
                artifact_classifier = classifier[0] if classifier else ''
                extension = snapshotArtifact.xpath("extension/text()")
                artifact_extension = extension[0] if extension else ''
                if artifact_classifier == artifact.classifier and artifact_extension == artifact.extension:
                    return self._uri_for_artifact(artifact, snapshotArtifact.xpath("value/text()")[0])
            timestamp_xmlpath = xml.xpath("/metadata/versioning/snapshot/timestamp/text()")
            if timestamp_xmlpath:
                timestamp = timestamp_xmlpath[0]
                build_number = xml.xpath("/metadata/versioning/snapshot/buildNumber/text()")[0]
                return self._uri_for_artifact(artifact, artifact.version.replace("SNAPSHOT", timestamp + "-" + build_number))

        return self._uri_for_artifact(artifact, artifact.version)

    def _uri_for_artifact(self, artifact, version=None):
        if artifact.is_snapshot() and not version:
            raise ValueError("Expected uniqueversion for snapshot artifact " + str(artifact))
        elif not artifact.is_snapshot():
            version = artifact.version
        if artifact.classifier:
            return posixpath.join(self.base, artifact.path(), artifact.artifact_id + "-" + version + "-" + artifact.classifier + "." + artifact.extension)

        return posixpath.join(self.base, artifact.path(), artifact.artifact_id + "-" + version + "." + artifact.extension)

    # for small files, directly get the full content
    def _getContent(self, url, failmsg, force=True):
        if self.local:
            parsed_url = urlparse(url)
            if os.path.isfile(parsed_url.path):
                with io.open(parsed_url.path, 'rb') as f:
                    return f.read()
            if force:
                raise ValueError(failmsg + " because can not find file: " + url)
            return None
        response = self._request(url, failmsg, force)
        if response:
            return response.read()
        return None

    # only for HTTP request
    def _request(self, url, failmsg, force=True):
        url_to_use = url
        parsed_url = urlparse(url)

        if parsed_url.scheme == 's3':
            parsed_url = urlparse(url)
            bucket_name = parsed_url.netloc
            key_name = parsed_url.path[1:]
            client = boto3.client('s3', aws_access_key_id=self.module.params.get('username', ''), aws_secret_access_key=self.module.params.get('password', ''))
            url_to_use = client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key_name}, ExpiresIn=10)

        req_timeout = self.module.params.get('timeout')

        # Hack to add parameters in the way that fetch_url expects
        self.module.params['url_username'] = self.module.params.get('username', '')
        self.module.params['url_password'] = self.module.params.get('password', '')
        self.module.params['http_agent'] = self.module.params.get('user_agent', None)

        response, info = fetch_url(self.module, url_to_use, timeout=req_timeout, headers=self.headers)
        if info['status'] == 200:
            return response
        if force:
            raise ValueError(failmsg + " because of " + info['msg'] + "for URL " + url_to_use)
        return None

    def download(self, tmpdir, artifact, verify_download, filename=None):
        if not artifact.version or artifact.version == "latest":
            artifact = Artifact(artifact.group_id, artifact.artifact_id, self.find_latest_version_available(artifact),
                                artifact.classifier, artifact.extension)
        url = self.find_uri_for_artifact(artifact)
        tempfd, tempname = tempfile.mkstemp(dir=tmpdir)

        try:
            # copy to temp file
            if self.local:
                parsed_url = urlparse(url)
                if os.path.isfile(parsed_url.path):
                    shutil.copy2(parsed_url.path, tempname)
                else:
                    return "Can not find local file: " + parsed_url.path
            else:
                response = self._request(url, "Failed to download artifact " + str(artifact))
                with os.fdopen(tempfd, 'wb') as f:
                    shutil.copyfileobj(response, f)

            if verify_download:
                invalid_md5 = self.is_invalid_md5(tempname, url)
                if invalid_md5:
                    # if verify_change was set, the previous file would be deleted
                    os.remove(tempname)
                    return invalid_md5
        except Exception as e:
            os.remove(tempname)
            raise e

        # all good, now copy temp file to target
        shutil.move(tempname, artifact.get_filename(filename))
        return None

    def is_invalid_md5(self, file, remote_url):
        if os.path.exists(file):
            local_md5 = self._local_md5(file)
            if self.local:
                parsed_url = urlparse(remote_url)
                remote_md5 = self._local_md5(parsed_url.path)
            else:
                try:
                    remote_md5 = to_text(self._getContent(remote_url + '.md5', "Failed to retrieve MD5", False), errors='strict')
                except UnicodeError as e:
                    return "Cannot retrieve a valid md5 from %s: %s" % (remote_url, to_native(e))
                if(not remote_md5):
                    return "Cannot find md5 from " + remote_url
            try:
                # Check if remote md5 only contains md5 or md5 + filename
                _remote_md5 = remote_md5.split(None)[0]
                remote_md5 = _remote_md5
                # remote_md5 is empty so we continue and keep original md5 string
                # This should not happen since we check for remote_md5 before
            except IndexError as e:
                pass
            if local_md5 == remote_md5:
                return None
            else:
                return "Checksum does not match: we computed " + local_md5 + "but the repository states " + remote_md5

        return "Path does not exist: " + file

    def _local_md5(self, file):
        md5 = hashlib.md5()
        with io.open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            group_id=dict(required=True),
            artifact_id=dict(required=True),
            version=dict(default="latest"),
            classifier=dict(default=''),
            extension=dict(default='jar'),
            repository_url=dict(default=None),
            username=dict(default=None, aliases=['aws_secret_key']),
            password=dict(default=None, no_log=True, aliases=['aws_secret_access_key']),
            headers=dict(type='dict'),
            state=dict(default="present", choices=["present", "absent"]),  # TODO - Implement a "latest" state
            timeout=dict(default=10, type='int'),
            dest=dict(type="path", required=True),
            validate_certs=dict(required=False, default=True, type='bool'),
            keep_name=dict(required=False, default=False, type='bool'),
            verify_checksum=dict(required=False, default='download', choices=['never', 'download', 'change', 'always'])
        ),
        add_file_common_args=True
    )

    if not HAS_LXML_ETREE:
        module.fail_json(msg=missing_required_lib('lxml'), exception=LXML_ETREE_IMP_ERR)

    repository_url = module.params["repository_url"]
    if not repository_url:
        repository_url = "http://repo1.maven.org/maven2"
    try:
        parsed_url = urlparse(repository_url)
    except AttributeError as e:
        module.fail_json(msg='url parsing went wrong %s' % e)

    local = parsed_url.scheme == "file"

    if parsed_url.scheme == 's3' and not HAS_BOTO:
        module.fail_json(msg=missing_required_lib('boto3', reason='when using s3:// repository URLs'),
                         exception=BOTO_IMP_ERR)

    group_id = module.params["group_id"]
    artifact_id = module.params["artifact_id"]
    version = module.params["version"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    headers = module.params['headers']
    state = module.params["state"]
    dest = module.params["dest"]
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    keep_name = module.params["keep_name"]
    verify_checksum = module.params["verify_checksum"]
    verify_download = verify_checksum in ['download', 'always']
    verify_change = verify_checksum in ['change', 'always']

    downloader = MavenDownloader(module, repository_url, local, headers)

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

    if os.path.lexists(b_dest) and ((not verify_change) or not downloader.is_invalid_md5(dest, downloader.find_uri_for_artifact(artifact))):
        prev_state = "present"

    if prev_state == "absent":
        try:
            download_error = downloader.download(module.tmpdir, artifact, verify_download, b_dest)
            if download_error is None:
                changed = True
            else:
                module.fail_json(msg="Cannot retrieve the artifact to destination: " + download_error)
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

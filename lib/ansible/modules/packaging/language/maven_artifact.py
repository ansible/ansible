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
short_description: Downloads an artifact from a maven repository.
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
            - The maven groupId coordinate.
        required: true
    artifact_id:
        description:
            - The maven artifactId coordinate.
        required: true
    version:
        description:
            - The maven version coordinate. Special value "release" is used to specify the latest available release.
        required: false
        default: latest
    classifier:
        description:
            - The maven classifier coordinate.
        required: false
        default: null
    extension:
        description:
            - The maven type/extension coordinate.
        required: false
        default: jar
    url_repository:
        version_added: "2.3"
        aliases: [ repository_url, repository ]
        description:
            - The URL of the maven Repository to download from.
            - Use s3://... if the repository is hosted on Amazon S3, added in version 2.2.
        required: false
        default: http://repo1.maven.org/maven2
    url_username:
        version_added: "2.3"
        aliases: [ username, user, uname, aws_secret_key ]
        description:
            - The username to authenticate as to the maven Repository, Use AWS secret key of the repository is hosted on S3.
        required: false
        default: null
    url_password:
        version_added: "2.3"
        aliases: [ password, pwd, passwd, aws_secret_access_key ]
        description:
            - The password to authenticate with to the maven Repository. Use AWS secret access key of the repository is hosted on S3.
        required: false
        default: null
    dest:
        description:
            - The path where the artifact should be written to.
        required: true
        default: false
    state:
        description:
            - The desired state of the artifact.
        required: true
        default: present
        choices: [ present, absent ]
    timeout:
        description:
            - Specifies a timeout in seconds for the connection attempt.
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
    ignore_checksum:
        version_added: "2.3"
        description:
            - If C(yes), the checksum verification after downloading will be ignored. May result in corrupt artifacts if the network connection fails, but enables downloading artifacts which don't have a remote checksum calculated.
        required: false
        default: 'no'
        choices: ['yes', 'no']
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
    repository_url: https://repo.company.com/maven
    username: user
    password: pass
    dest: /tmp/library-name-latest.jar
# Download a WAR File to the Tomcat webapps directory to be deployed
- maven_artifact:
    group_id: com.company
    artifact_id: web-app
    extension: war
    repository_url: https://repo.company.com/maven
    dest: /var/lib/tomcat7/webapps/web-app.war
# Passing a directory as destination, the filename will contain the artifact_id, version and classifier
- maven_artifact:
    version: latest
    artifact_id: spring-core
    group_id: org.springframework
    dest: /tmp/
# Copy a WAR file from the local maven repository to the Tomcat webapps directory to be deployed
- maven_artifact:
    group_id: com.company
    artifact_id: web-app
    extension: war
    repository_url: file://home/jenkins/.m2/repository
    dest: /var/lib/tomcat7/webapps/web-app.war
'''

import lxml.etree as etree
import os
import hashlib
import os
import posixpath
import shutil
import distutils.version
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
import urlparse # Override urlparse from module_utils
try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.urls import fetch_url


class Artifact(object):
    def __init__(self, group_id, artifact_id, version, classifier=None, extension='jar'):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version
        self.classifier = classifier
        self.extension = extension

    @property
    def url(self):
        return posixpath.join(self.group_id.replace(".", "/"), self.artifact_id, self.version, self.filename)

    @property
    def filename(self):
        bits = [self.artifact_id, self.version]
        if self.classifier:
            bits.append(self.classifier)
        return "-".join(bits) + "." + self.extension


class HttpMavenClient:
    def __init__(self, module, repository, timeout):
        self.module = module
        self.repo = repository.rstrip("/")
        self.timeout = timeout

    def get(self, url):
        url = posixpath.join(self.repo, url)
        if url.startswith("s3://"):
            parsed_url = urlparse.urlparse(url)
            bucket = parsed_url.netloc[:parsed_url.netloc.find('.')]
            key_name = parsed_url.path[1:]
            user = self.module.params.get('url_username', '')
            password = self.module.params.get('url_password', '')
            client = boto3.client('s3', aws_access_key_id=user, aws_secret_access_key=passwd)
            url = client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key_name }, ExpiresIn=10)

        response, info = fetch_url(self.module, url, timeout=self.timeout)
        if info['status'] != 200:
            raise Exception("Unable to complete request (%s)" % (url))
        return response.read()

    def download_metadata(self, artifact):
        url = "%s/maven-metadata.xml" % (posixpath.join(*artifact.url.split("/")[0:-2]))
        response = self.get(url)
        return etree.fromstring(response)

    def get_latest_version(self, artifact):
        # We are trusting the order returned by the XML, but should we?
        return str(self.download_metadata(artifact).xpath("/metadata/versioning/versions/version[last()]/text()")[-1])

    def get_release_version(self, artifact):
        return str(self.download_metadata(artifact).xpath("/metadata/versioning/release/text()")[-1])

    def get_md5(self, artifact):
        return self.get(artifact.url + '.md5')

    def download(self, artifact, destination):
        if os.path.isdir(destination) or destination.endswith("/"):
            destination = os.path.join(destination, artifact.filename)
        with open(destination, 'w') as file:
            response = self.get(artifact.url)
            file.write(response)
        return destination

    def checksum(self, artifact, dest):
        if not os.path.isfile(dest):
            return False
        remote_md5 = self.get_md5(artifact)
        local_md5 = None
        with open(dest, 'rb') as file:
            local_md5 = hashlib.md5(file.read()).hexdigest()

        return remote_md5 == local_md5

class FileSystemMavenClient:
    def __init__(self, module, repository, timeout=None):
        self.module = module
        self.repo = repository.rstrip("/")

    def get_latest_version(self, artifact):
        path = posixpath.join(self.repo, artifact.group_id.replace(".", "/"), artifact.artifact_id).replace('file:/', '')
        versions = []
        for root, dirs, files in os.walk(path):
            for d in dirs:
                versions.append(d)
        if not versions:
            self.module.fail_json(msg='Unable to find any version for: %s' % (':'.join([artifact.group_id, artifact.artifact_id, artifact.classifier, artifact.extension])))
        return sorted(versions, key=distutils.version.LooseVersion)[-1]

    def get_release_version(self, artifact):
        path = posixpath.join(self.repo, artifact.group_id.replace(".", "/"), artifact.artifact_id).replace('file:/', '')
        versions = []
        for root, dirs, files in os.walk(path):
            for d in dirs:
                if '-SNAPSHOT' in dirs:
                    continue
                versions.append(d)
        if not versions:
            self.module.fail_json(msg='Unable to find any version for: %s' % (':'.join([artifact.group_id, artifact.artifact_id, artifact.classifier, artifact.extension])))
        return sorted(versions, key=distutils.version.LooseVersion)[-1]

    def download(self, artifact, destination):
        try:
            src = posixpath.join(self.repo, artifact.url).replace('file:/', '').replace('//', '/')
            return shutil.copy2(src, destination)
        except (IOError, os.error) as why:
            self.module.fail_json(msg='Copy failed. %s' % (':'.join([artifact.group_id, artifact.artifact_id, artifact.classifier, artifact.extension, artifact.url, destination, str(why)])))

    def checksum(self, artifact, dest):
        self.module.fail_json(msg=artifact.url)
        return True # There is nothing to check if the artifact is local


def main():

    module = AnsibleModule(
        argument_spec = dict(
            group_id = dict(required=True),
            artifact_id = dict(required=True),
            version = dict(default='latest'),
            classifier = dict(default=None),
            extension = dict(default='jar'),
            url_repository = dict(default='http://repo1.maven.org/maven2', aliases=['repository_url', 'repository']),
            url_username = dict(default=None, aliases=['username', 'user', 'uname', 'aws_secret_key']),
            url_password = dict(default=None, aliases=['password', 'pwd', 'passwd', 'aws_secret_access_key'], no_log=True),
            http_agent = dict(default='Maven Artifact Downloader/1.0'),
            state = dict(default='present', choices=['present','absent']),
            dest = dict(type='path', default=None),
            timeout = dict(default=10, type='int'),
            validate_certs = dict(default=True, type='bool'),
            ignore_checksum = dict(default=False, type='bool'),
        )
    )


    try:
        parsed_url = urlparse(url_repository)
    except AttributeError as e:
        module.fail_json(msg='url parsing went wrong %s' % e)

    if parsed_url.scheme=='s3' and not HAS_BOTO:
        module.fail_json(msg='boto3 required for this module, when using s3:// repository URLs')

    group_id = module.params["group_id"]
    artifact_id = module.params["artifact_id"]
    version = module.params["version"]
    classifier = module.params["classifier"]
    extension = module.params["extension"]
    repo = module.params["url_repository"]
    state = module.params["state"]
    dest = module.params["dest"]
    timeout = module.params["timeout"]
    ignore_checksum = module.params["ignore_checksum"]

    if repo.startswith("s3://") and not HAS_BOTO:
        module.fail_json(msg='boto3 required when using s3:// repository URLs with this module.')
    elif repo.startswith('file://'):
        client = FileSystemMavenClient(module, repo, timeout)
    else:
        client = HttpMavenClient(module, repo, timeout)
    artifact = Artifact(group_id, artifact_id, version, classifier, extension)

    try:
        if version == 'latest':
            artifact.version = client.get_latest_version(artifact)
        elif version == 'release':
            artifact.version = client.get_release_version(artifact)
    except Exception as e:
        module.fail_json(msg=e.args[0])

    if not artifact.version:
        module.fail_json(msg="Unable to retrieve version number. Is the version number valid? Is it a snapshot-only repository?")

    if os.path.isdir(dest):
        dest = os.path.join(dest, artifact.filename)

    # Should we delete the file?
    if state == 'absent':
        if os.path.isfile(dest):
            os.remove(dest)
            module.exit_json(dest=dest, state=state, changed=True)
        else:
            module.exit_json(dest=dest, state=state, changed=False)

    # Does the local file already exist and match the remote md5?
    if client.checksum(artifact, dest):
        module.exit_json(dest=dest, state=state, version=artifact.version, changed=False)

    try:
        client.download(artifact, dest)
    except Exception as e:
        module.fail_json(msg=e.args[0])

    if ignore_checksum and not client.checksum(artifact, dest):
        module.fail_json(msg="I was able to download the artifact (%s), but the checksum doesn't match (%s)." % (artifact.url, dest))

    module.exit_json(state=state, dest=dest, group_id=group_id, artifact_id=artifact_id,
                     version=artifact.version, classifier=classifier, extension=extension,
                     url_repository=repo, ignore_checksum=ignore_checksum, changed=True)

if __name__ == '__main__':
    main()

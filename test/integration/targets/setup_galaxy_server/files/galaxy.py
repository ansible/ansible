#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import configparser
import datetime
import errno
import hashlib
import json
import os
import os.path
import re
import semantic_version
import shutil
import tarfile
import threading

from flask import (
    Flask,
    request,
    send_file,
)

from flask_sqlalchemy import (
    SQLAlchemy,
)

from functools import (
    wraps,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

config_path = os.path.abspath(os.path.expanduser(os.path.expandvars(
    os.environ.get('GALAXY_CONFIG', os.path.join(os.path.dirname(__file__), 'galaxy.ini'))))
)
config = configparser.ConfigParser()
config.read(config_path)


def get_config(option, default=None):
    try:
        return config.get('default', option)
    except configparser.NoOptionError:
        return default


COLLECTIONS_DIR = os.path.abspath(os.path.expanduser(os.path.expandvars(
    get_config('collections_dir', os.path.join(os.path.dirname(__file__), 'collections'))
)))
AUTH_TOKEN = get_config('token')
IMPORT_TMP = os.path.join(os.path.dirname(__file__), 'tmp-import')
GALAXY_PORT = get_config('port', 41645)
PAGINATION_COUNT = int(get_config('pagination_count', 5))


class Namespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, unique=True, nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    modified = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return '<Namespace %s>' % self.name

    def get_api_info(self):
        return {
            'id': self.id,
            'url': '/api/v1/namespaces/%s/' % self.id,
            'name': self.name,
            'active': True,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def get_api_reference(self):
        return {
            'id': self.id,
            'href': '%sapi/v1/namespaces/%s/' % (request.host_url, self.id),
            'name': self.name,
        }


class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    namespace_id = db.Column(db.Integer, db.ForeignKey('namespace.id'), nullable=False)
    namespace = db.relationship('Namespace', backref=db.backref('collections', lazy=True))
    deprecated = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    modified = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return '<Collection %s.%s>' % (self.namespace.name, self.name)

    def get_api_info(self):
        collection_reference = self.get_api_reference()
        url = collection_reference['href']
        latest_version = str(sorted([semantic_version.Version(v.version) for v in self.versions])[-1])

        return {
            'id': self.id,
            'href': url,
            'name': self.name,
            'namespace': self.namespace.get_api_reference(),
            'versions_url': '%sversions/' % url,
            'latest_version': {
                'version': latest_version,
                'href': '%sversions/%s/' % (url, latest_version),
            },
            'deprecated': self.deprecated,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def get_api_reference(self):
        url = '%sapi/v2/collections/%s/%s/' % (request.host_url, self.namespace.name, self.name)
        return {
            'id': self.id,
            'href': url,
            'name': self.name,
        }

    def get_api_versions(self):
        url = self.get_api_reference()['href']
        return [{'version': v.version, 'href': '%sversions/%s/' % (url, v.version)} for v in self.versions]

    @staticmethod
    def get_collection(namespace, name):
        namespace_info = Namespace.query.filter_by(name=namespace).first()
        if not namespace_info:
            return

        return Collection.query.with_parent(namespace_info).filter_by(name=name).first()


class CollectionVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    collection_filename = db.Column(db.UnicodeText, nullable=False)
    collection_size = db.Column(db.Integer, nullable=False)
    collection_hash = db.Column(db.UnicodeText, nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    collection = db.relationship('Collection', backref=db.backref('versions', lazy=True))
    version = db.Column(db.UnicodeText, nullable=False)
    hidden = db.Column(db.Boolean, default=False)

    # metadata
    tags = db.Column(db.UnicodeText)  # List as json string
    issues = db.Column(db.UnicodeText)
    readme = db.Column(db.UnicodeText)
    authors = db.Column(db.UnicodeText)  # List as json string
    license = db.Column(db.UnicodeText)  # List as json string
    homepage = db.Column(db.UnicodeText)
    repository = db.Column(db.UnicodeText)
    description = db.Column(db.UnicodeText)
    dependencies = db.Column(db.UnicodeText)  # Dict as json string
    licence_file = db.Column(db.UnicodeText)
    documentation = db.Column(db.UnicodeText)

    def __repr__(self):
        return '<CollectionVersion %s.%s:%s>' % (self.collection.namespace.name, self.collection.name, self.version)

    def get_api_info(self):
        collection_ref = self.collection.get_api_reference()
        url = '%sversions/%s/' % (collection_ref['href'], self.version)
        metadata = {
            'name': self.collection.name,
            'tags': json.loads(self.tags) if self.tags else [],
            'issues': self.issues,
            'readme': self.readme,
            'authors': json.loads(self.authors) if self.authors else [],
            'license': json.loads(self.license) if self.license else [],
            'version': self.version,
            'homepage': self.homepage,
            'namespace': self.collection.namespace.name,
            'repository': self.repository,
            'description': self.description,
            'dependencies': json.loads(self.dependencies) if self.dependencies else {},
            'license_file': self.licence_file,
            'documentation': self.documentation,
        }

        return {
            'id': self.id,
            'href': url,
            'download_url': '%sapi/custom/collections/%s' % (request.host_url, self.collection_filename),
            'artifact': {
                'filename': self.collection_filename,
                'size': self.collection_size,
                'sha256': self.collection_hash,
            },
            'namespace': self.collection.namespace.get_api_reference(),
            'collection': self.collection.get_api_reference(),
            'version': self.version,
            'hidden': self.hidden,
            'metadata': metadata,
        }

    @staticmethod
    def get_collection_version(namespace, name, version):
        namespace_info = Namespace.query.filter_by(name=namespace).first()
        if not namespace_info:
            return

        info = Collection.query.with_parent(namespace_info).filter_by(name=name).first()
        if not info:
            return

        return CollectionVersion.query.with_parent(info).filter_by(version=version).first()


class ImportTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, default=datetime.datetime.now)
    finished_at = db.Column(db.DateTime)
    state = db.Column(db.UnicodeText, default="waiting")
    error_code = db.Column(db.UnicodeText)
    error_msg = db.Column(db.UnicodeText)
    messages = db.Column(db.UnicodeText)  # list of dicts as json string.

    def __repr__(self):
        return '<ImportTask %s>' % self.id


class GalaxyImportError(Exception):

    def __init__(self, message, code):
        super(GalaxyImportError, self).__init__(message)
        self.code = code


def get_file_hash(path):
    buffer_size = 65536
    sha256 = hashlib.sha256()

    with open(path, mode='rb') as fd:
        while True:
            data = fd.read(buffer_size)
            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def get_tar_hash(tar, name):
    sha256 = hashlib.sha256()

    with tar.extractfile(tar.getmember(name)) as fd:
        sha256.update(fd.read())

    return sha256.hexdigest()


def insert_collection(manifest, filename, collection_size, collection_hash):
    if not Namespace.query.filter_by(name=manifest['namespace']).first():
        db.session.add(Namespace(name=manifest['namespace']))
    namespace = Namespace.query.filter_by(name=manifest['namespace']).first()

    if not Collection.query.filter_by(name=manifest['name']).first():
        db.session.add(Collection(name=manifest['name'], namespace=namespace))
    collection = Collection.query.filter_by(name=manifest['name']).first()

    version_kwargs = {}

    for k in ['issue', 'readme', 'homepage', 'repository', 'description', 'licence_file', 'documentation']:
        value = manifest.get(k, None)
        if value:
            version_kwargs[k] = value

    for k in ['tags', 'authors', 'license']:
        value = manifest.get(k, None)
        if value:
            version_kwargs[k] = json.dumps(value)

    for k in ['dependencies']:
        value = manifest.get(k, None)
        if value:
            version_kwargs[k] = json.dumps(value)

    db.session.add(CollectionVersion(
        collection_filename=filename,
        collection_size=collection_size,
        collection_hash=collection_hash,
        collection=collection,
        version=manifest['version'],
        **version_kwargs
    ))


def json_pagination_response(results, full_link=True):
    base_url = request.base_url if full_link else request.url_rule

    page_num = 1
    if request.query_string.startswith(b'page='):
        page_num = int(re.findall(b'page=(\\d+)', request.query_string)[0])

    previous_link = None
    displayed_results = 0
    if page_num > 1:
        previous_link = '%s?page=%d' % (base_url, page_num - 1)
        displayed_results = (page_num - 1) * PAGINATION_COUNT

    next_link = None
    if len(results) > (displayed_results + PAGINATION_COUNT):
        next_link = '%s?page=%d' % (base_url, page_num + 1)

    result_subset = results[displayed_results:displayed_results + PAGINATION_COUNT]

    if len(result_subset) == 0 and page_num != 1:
        return json_response({'code': 'not_found', 'message': 'Invalid page.'}, code=404)

    return json_response({
        'count': len(results),
        'next': next_link,
        'next_link': next_link,
        'previous': previous_link,
        'previous_link': previous_link,
        'results': result_subset,
    })


def json_response(data, code=200):
    return json.dumps(data), code, {'Content-Type': 'application/json'}


def load_collections(collections_dir):
    db.create_all()

    for name in os.listdir(collections_dir):
        tar_path = os.path.join(collections_dir, name)
        if os.path.isdir(tar_path):
            continue
        elif not tarfile.is_tarfile(tar_path):
            continue

        sha256_hash = get_file_hash(tar_path)

        print("INFO - Importing existing collection at '%s'" % tar_path)
        with tarfile.open(tar_path, mode='r') as collection_tar:
            try:
                manifest_file = collection_tar.getmember('MANIFEST.json')
            except KeyError:
                continue

            with collection_tar.extractfile(manifest_file) as manifest_fd:
                b_manifest_json = manifest_fd.read()

            manifest = json.loads(b_manifest_json.decode('utf-8'))['collection_info']
            insert_collection(manifest, name, os.path.getsize(tar_path), sha256_hash)

    db.session.commit()
    print("INFO - Import complete")


def login_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth and auth != 'Token %s' % AUTH_TOKEN:
            return '{"detail":"Invalid token."}', 401, {'Content-Type': 'application/json'}

        return f(*args, **kwargs)
    return decorated


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return '{"code":"not_authenticated","message":"Authentication credentials were not provided."}', 401, \
                   {'Content-Type': 'application/json'}
        elif auth != 'Token %s' % AUTH_TOKEN:
            return '{"detail":"Invalid token."}', 401, {'Content-Type': 'application/json'}

        return f(*args, **kwargs)
    return decorated


def process_form_data(value):
    value = value.strip()
    disposition_index = value.find(b';')
    content_disposition = value[:disposition_index].split(b':')[-1].strip().decode('utf-8')
    form_data = value[disposition_index + 1:].strip()

    disposition_params = re.split(b'[\r\n]+', form_data, 1)

    headers = {}
    for b_header in disposition_params[0].split(b';'):
        header_split = b_header.decode('utf-8').split('=', 2)
        headers[header_split[0].strip()] = header_split[1].strip('"')

    ext_value = disposition_params[1]

    return content_disposition, headers, ext_value


def process_import(import_id, collection_path):
    """ Very basic collection validation. """
    import_task = ImportTask.query.filter_by(id=import_id).first()
    messages = [{'level': 'INFO', 'message': 'Starting import: task_id=%s' % import_id,
                 'time': datetime.datetime.now().isoformat()}]

    try:
        if not tarfile.is_tarfile(collection_path):
            raise GalaxyImportError("Uploaded collection is not a tar file", "GALAXY0001")

        collection_hash = get_file_hash(collection_path)

        with tarfile.open(collection_path, mode='r') as collection_tar:
            required_files = {'MANIFEST.json': None, 'FILES.json': None}
            for required_file in required_files.keys():
                try:
                    json_tar_fd = collection_tar.getmember(required_file)
                except KeyError:
                    raise GalaxyImportError("Missing the %s file" % required_file, "GALAXY0002")

                with collection_tar.extractfile(json_tar_fd) as json_fd:
                    b_json = json_fd.read()

                try:
                    required_json = json.loads(b_json.decode('utf-8'))
                except ValueError:
                    raise GalaxyImportError("Manifest file %s is not valid json" % required_file, "GALAXY0003")

                actual_format_version = required_json.get('format')
                if actual_format_version != 1:
                    raise GalaxyImportError("Invalid format for manifest file %s" % required_file, "GALAXY0004")

                required_files[required_file] = required_json

            for file_type, valid_keys in [('MANIFEST.json', ['collection_info', 'file_manifest_file', 'format']),
                                          ('FILES.json', ['files', 'format'])]:
                actual_keys = sorted(required_files[file_type].keys())
                if actual_keys != valid_keys:
                    raise GalaxyImportError("Invalid keys in %s" % file_type, "GALAXY005")

            required_keys = ['namespace', 'name', 'version', 'readme', 'authors']
            manifest_json = required_files['MANIFEST.json']
            for key in required_keys:
                if key not in manifest_json['collection_info']:
                    raise GalaxyImportError("Missing required key %s" % key, "GALAXY006")

            actual_files_hash = get_tar_hash(collection_tar, 'FILES.json')
            if actual_files_hash != manifest_json['file_manifest_file']['chksum_sha256']:
                raise GalaxyImportError("FILES.json checksum mismatch", "GALAXY007")

            for file_entry in required_files['FILES.json']['files']:
                file_name = file_entry['name']
                if file_name in ['.', '..'] or file_entry['ftype'] == 'dir':
                    continue

                actual_hash = get_tar_hash(collection_tar, file_name)
                if actual_hash != file_entry['chksum_sha256']:
                    raise GalaxyImportError("%s checksum mismatch" % file_name, "GALAXY007")

            # We've validated what we can, add the collection to the in memory db.
            insert_collection(manifest_json['collection_info'], os.path.basename(collection_path),
                              os.path.getsize(collection_path), collection_hash)

        os.rename(collection_path, os.path.join(COLLECTIONS_DIR, os.path.basename(collection_path)))
        import_task.state = 'finished'
    except GalaxyImportError as e:
        import_task.state = 'failed'
        import_task.error_code = e.code
        import_task.error_msg = str(e)

        msg = {
            'level': 'ERROR',
            'message': 'Import Task "%s" failed: %s' % (import_id, str(e)),
            'time': datetime.datetime.now().isoformat()
        }
        messages.append(msg)
    except Exception as e:
        import_task.state = 'failed'
        import_task.error_code = 'GALAXYUNKNOWN'
        import_task.error_msg = str(e)

        msg = {
            'level': 'ERROR',
            'message': 'Import Task "%s" failed: Unknown error when validating collection: %s' % (import_id, str(e)),
            'time': datetime.datetime.now().isoformat(),
        }
        messages.append(msg)
    finally:
        import_task.finished_at = datetime.datetime.now()
        import_task.messages = json.dumps(messages)
        db.session.commit()


@app.route('/api/')
@login_optional
def api():
    return json_response({
        'description': 'GALAXY REST API',
        'current_version': 'v1',
        'available_versions': {
            'v1': 'v1/',
            'v2': 'v2/',
        },
        'server_version': '3.3.4',
        'version_name': 'Doin'' it Right',
        'team_members': [
            'jborean93'
        ]
    })


@app.route('/api/custom/collections/<filename>')
@login_optional
def get_collection_download(filename):
    file_path = os.path.join(COLLECTIONS_DIR, filename)
    if not os.path.exists(file_path):
        response = {
            'code': 'not_found',
            'message': "Artifact '%s' does not exist." % filename,
        }
        return json_response(response, code=404)

    return send_file(file_path, as_attachment=True)


@app.route('/api/v1/namespaces/')
@login_optional
def namespaces():
    return json_pagination_response([n.get_api_info() for n in Namespace.query.all()], full_link=False)


@app.route('/api/v1/namespaces/<namespace_id>/')
@login_optional
def namespaces_id(namespace_id):
    namespace = Namespace.query.filter_by(id=namespace_id).first()
    if not namespace:
        return json_response({'detail': 'Not found.'}, code=404)

    return json_response(namespace.get_api_info())


@app.route('/api/v2/collection-imports/<import_id>/')
@login_required
def collection_imports(import_id):
    import_task = ImportTask.query.filter_by(id=import_id).first()
    if not import_task:
        return json_response({'code': 'not_found', 'message': 'Not found.'}, code=404)

    response = {
        'id': import_id,
        'started_at': import_task.started_at.isoformat(),
        'finished_at': import_task.finished_at.isoformat() if import_task.finished_at else None,
        'state': import_task.state,
        'error': None,
        'messages': json.loads(import_task.messages) if import_task.messages else [],
    }

    if import_task.error_code or import_task.error_msg:
        response['error'] = {
            'code': import_task.error_code or 'UNKNOWN',
            'description': import_task.error_msg or 'Unknown error',
        }

    return json_response(response)


@app.route('/api/v2/collections/', methods=['GET'])
@login_optional
def collections_get():
    return json_pagination_response([c.get_api_info() for c in Collection.query.all()], full_link=False)


@app.route('/api/v2/collections/', methods=['POST'])
@login_required
def collections_post():
    # Flask does not seem to parse the form data properly, will need to do it manually.
    post_data = request.get_data()

    content_length = request.headers.get('Content-Length')
    content_type_header = request.headers.get('Content-Type')

    if not content_length or not content_type_header:
        response = {
            'code': 'invalid',
            'message': 'Invalid input.',
            'errors': [
                {'code': 'required', 'message': 'No file was submitted.', 'field': 'file'},
            ]
        }
        return json_response(response, code=400)

    content_type, boundary = content_type_header.split(';')
    if content_type != 'multipart/form-data':
        response = {
            'code': 'unsupported media type',
            'message': 'Unsupported media type "%s" in request.' % content_type_header,
        }
        return json_response(response, code=415)

    boundary = re.findall(r'boundary=([\x00-\x7f]*)', boundary)[0]  # Boundary can take in any 7-bit ASCII chars.
    if not boundary:
        response = {
            'code': 'parse_error',
            'message': 'Multipart form parse error - Invalid boundary in multipart: ',
        }
        return json_response(response, code=400)

    # The boundary start and end is defined by 2 hyphen, ignore that when splitting the form data.
    form_data = [process_form_data(v) for v in post_data.split(b'--' + boundary.encode('ascii')) if v and v != b'--']

    # Verify the expected hash is there
    if form_data[0][0] != 'form-data' or 'name' not in form_data[0][1] or form_data[0][1]['name'] != 'sha256':
        response = {
            'code': 'parse_error',
            'message': 'Multipart form parse error - Missing form-data with sha256 hash',
        }
        return json_response(response, code=400)
    expected_hash = form_data[0][2].decode('ascii')

    # Verify the file data is there
    if form_data[1][0] != 'file' or 'filename' not in form_data[1][1]:
        response = {
            'code': 'parse_error',
            'message': 'Multipart form parse error - Missing file with filename',
        }
        return json_response(response, code=400)
    filename = form_data[1][1]['filename']

    # The actual collection bytes is preset after the first 2 newlines, read that and place it into a temporary file.
    b_collection_tar = form_data[1][2].split(b'\r\n', 2)[2]
    sha256 = hashlib.sha256()
    import_path = os.path.join(IMPORT_TMP, filename)
    with open(import_path, mode='wb') as import_fd:
        sha256.update(b_collection_tar)
        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            response = {
                'code': 'invalid',
                'message': 'Invalid input.',
                'errors': [
                    {'code': 'checksum_mismatch', 'message': 'The expected hash did not match the actual hash.'},
                ]
            }
            return json_response(response, code=400)

        import_fd.write(b_collection_tar)

    import_task = ImportTask()
    db.session.add(import_task)
    db.session.commit()

    import_uri = '%sapi/v2/collection-imports/%s/' % (request.host_url, import_task.id)
    import_thread = threading.Thread(target=process_import, args=(import_task.id, filename))
    import_thread.daemon = True
    import_thread.start()

    return json_response({'task': import_uri})


@app.route('/api/v2/collections/<namespace>/<name>/')
@login_optional
def collection_info(namespace, name):
    collection = Collection.get_collection(namespace, name)
    if not collection:
        return json_response({'code': 'not_found', 'message': 'Not found.'}, code=404)

    return json_response(collection.get_api_info())


@app.route('/api/v2/collections/<namespace>/<name>/versions/')
@login_optional
def collection_versions(namespace, name):
    collection = Collection.get_collection(namespace, name)
    if not collection:
        return json_response({'code': 'not_found', 'message': 'Not found.'}, code=404)

    return json_pagination_response(collection.get_api_versions())


@app.route('/api/v2/collections/<namespace>/<name>/versions/<version>/')
@login_optional
def collection_version(namespace, name, version):
    version_info = CollectionVersion.get_collection_version(namespace, name, version)
    if not version_info:
        return json_response({'code': 'not_found', 'message': 'Not found.'}, code=404)

    return json_response(version_info.get_api_info())


def main():
    load_collections(COLLECTIONS_DIR)
    if not os.path.isdir(IMPORT_TMP):
        os.mkdir(IMPORT_TMP)

    pidfile = os.path.splitext(__file__)[0] + '.pid'
    with open(pidfile, mode='w') as fd:
        fd.write(str(os.getpid()))

    try:
        app.run('0.0.0.0', GALAXY_PORT, debug=True, threaded=True)
    finally:
        try:
            os.remove(pidfile)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise

        shutil.rmtree(IMPORT_TMP, ignore_errors=True)


if __name__ == '__main__':
    main()


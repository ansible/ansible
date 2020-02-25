#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
import uuid

from flask import (
    Flask,
    redirect,
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
# app.config['SQLALCHEMY_ECHO'] = True
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

# THIS IS A BAD HACK! No idea why buy querying and updating the ImportTask table in another thread puts the database
# in a bad state. Instead just keep track of the imports in a simple dictionary
IMPORT_LOCK = threading.Lock()
IMPORT_TABLE = {}


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

    def get_api_info(self, api_version):
        latest_version = str(sorted([semantic_version.Version(v.version) for v in self.versions])[-1])
        return getattr(self, '_get_api_info_%s' % api_version)(latest_version)

    def _get_api_info_v2(self, latest_version):
        collection_reference = self.get_api_reference()
        url = collection_reference['href']

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

    def _get_api_info_v3(self, latest_version):
        url = '/api/automation-hub/v3/collections/%s/%s/' % (self.namespace.name, self.name)
        return {
            'href': url,
            'created_at': self.created.isoformat(),
            'modified_at': self.modified.isoformat(),
            'namespace': self.namespace.name,
            'name': self.name,
            'deprecated': self.deprecated,
            'versions_url': '%sversions/' % url,
            'highest_version': {
                'href': '%sversions/%s/' % (url, latest_version),
                'versions': latest_version,
            }
        }

    def get_api_reference(self):
        url = '%sapi/v2/collections/%s/%s/' % (request.host_url, self.namespace.name, self.name)
        return {
            'id': self.id,
            'href': url,
            'name': self.name,
        }

    def get_api_versions(self, api_version):
        return getattr(self, '_get_api_versions_%s' % api_version)()

    def _get_api_versions_v2(self):
        url = self.get_api_reference()['href']
        return [{'version': v.version, 'href': '%sversions/%s/' % (url, v.version)} for v in self.versions]

    def _get_api_versions_v3(self):
        url = '/api/automation-hub/v3/collections/%s/%s/versions/' % (self.namespace.name, self.name)
        return [{
            'version': v.version,
            'certification': 'certified',
            'href': '%s%s/' % (url, v.version),
            'created_at': v.created.isoformat(),
            'updated_at': v.modified.isoformat(),
        } for v in self.versions]

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
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    modified = db.Column(db.DateTime, default=datetime.datetime.now)

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

    def get_api_info(self, api_version):
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

        base_info = {
            'download_url': '%sapi/custom/collections/%s' % (request.host_url, self.collection_filename),
            'artifact': {
                'filename': self.collection_filename,
                'size': self.collection_size,
                'sha256': self.collection_hash,
            },
            'namespace': self.collection.namespace.get_api_reference(),
            'collection': self.collection.get_api_reference(),
            'version': self.version,
            'metadata': metadata,
        }

        return getattr(self, '_get_api_info_%s' % api_version)(base_info)

    def _get_api_info_v2(self, base_info):
        collection_ref = self.collection.get_api_reference()
        url = '%sversions/%s/' % (collection_ref['href'], self.version)

        base_info['id'] = self.id
        base_info['href'] = url
        base_info['hidden'] = self.hidden

        return base_info

    def _get_api_info_v3(self, base_info):
        url = '/api/automation-hub/v3/collections/%s/%s/' % (self.collection.namespace.name, self.collection.name)
        base_info['certification'] = 'certified'
        base_info['href'] = '%sversions/%s/' % (url, self.version)
        base_info['created_at'] = self.created.isoformat()
        base_info['updated_at'] = self.modified.isoformat()
        base_info['collection']['href'] = url
        base_info['namespace'] = {'name': self.collection.namespace.name}
        base_info['metadata']['contents'] = []

        return base_info

    @staticmethod
    def get_collection_version(namespace, name, version):
        namespace_info = Namespace.query.filter_by(name=namespace).first()
        if not namespace_info:
            return

        info = Collection.query.with_parent(namespace_info).filter_by(name=name).first()
        if not info:
            return

        return CollectionVersion.query.with_parent(info).filter_by(version=version).first()


class ImportTask(object):

    def __init__(self, id):
        self.id = id
        self.started_at = datetime.datetime.now()
        self.finished_at = None
        self.state = 'waiting'
        self.error_code = None
        self.error_msg = None
        self.messages = []

    def __repr__(self):
        return '<ImportTask %s>' % self.id

    def get_api_info(self, api_version):
        base_info = {
            'id': self.id,
            'started_at': self.started_at.isoformat(),
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'state': self.state,
            'error': None,
        }

        return getattr(self, '_get_api_info_%s' % api_version)(base_info)

    def _get_api_info_v2(self, base_info):
        base_info['messages'] = self.messages

        if self.error_code or self.error_msg:
            base_info['error'] = {
                'code': self.error_code or 'UNKNOWN',
                'description': self.error_msg or 'Unknown error',
            }

        return base_info

    def _get_api_info_v3(self, base_info):
        base_info['created_at'] = base_info['started_at']
        base_info['updated_at'] = base_info['finished_at'] or base_info['started_at']

        if self.error_code or self.error_msg:
            base_info['error'] = {
                'description': self.error_msg or (self.error_code or 'Unknown error'),
            }

        return base_info


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

    if not Collection.query.with_parent(namespace).filter_by(name=manifest['name']).first():
        db.session.add(Collection(name=manifest['name'], namespace=namespace))
    collection = Collection.query.with_parent(namespace).filter_by(name=manifest['name']).first()

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
    db.session.commit()


def json_galaxy_error(api_version, code, message, title=None, status=400):
    if api_version == 'v2':
        return json_response({'code': code, 'message': message}, code=status)
    else:
        title = title or message
        return json_response({
            'errors': [
                {'status': status, 'code': code, 'title': title, 'detail': message}
            ]
        }, code=status)


def json_not_found_response(api_version):
    return json_galaxy_error(api_version, 'not_found', 'Not found.', status=404)


def json_pagination_response(results, api_version, full_link=True):
    if api_version == 'v2':
        base_url = request.base_url if full_link else request.path

        page_num = 1
        if request.query_string.startswith(b'page='):
            page_num = int(re.findall(b'page=(\\d+)', request.query_string)[0])

        previous_link = None
        displayed_results = 0
        if page_num > 1:
            displayed_results = (page_num - 1) * PAGINATION_COUNT
            previous_link = '%s?page=%d' % (base_url, page_num - 1)

        result_subset = results[displayed_results:displayed_results + PAGINATION_COUNT]

        next_link = None
        if len(results) > (displayed_results + PAGINATION_COUNT):
            next_link = '%s?page=%d' % (base_url, page_num + 1)

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
    else:
        base_url = request.path

        limit = PAGINATION_COUNT
        offset = 0
        query_match = re.match(b'limit=(\\d+)(&offset=(\\d+))*', request.query_string)
        if query_match:
            limit = int(query_match.group(1))
            offset = int(query_match.group(3) or 0)

        previous_link = None
        if offset > 0:
            previous_link = '%s?limit=%d' % (base_url, limit)

            if offset > limit:
                previous_link += '&offset=%d' % (offset - limit,)

        next_link = None
        if offset + limit <= len(results):
            next_link = '%s?limit=%d&offset=%s' % (base_url, limit, offset + limit)

        last_count = len(results) - PAGINATION_COUNT if len(results) > PAGINATION_COUNT else 0
        return json_response({
            'meta': {
                'count': len(results),
            },
            'links': {
                'first': '%s/?limit=%d&offset=0' % (base_url, limit),
                'previous': previous_link,
                'next': next_link,
                'last': '%s/?limit=%d&offset=%d' % (base_url, limit, last_count),
            },
            'data': results[offset:offset + limit],
        })


def json_response(data, code=200):
    return json.dumps(data), code, {'Content-Type': 'application/json'}


def start_up(clear=False):
    if clear:
        shutil.rmtree(COLLECTIONS_DIR)
        os.mkdir(COLLECTIONS_DIR)

    db.drop_all()
    global IMPORT_TABLE
    IMPORT_TABLE = {}
    db.create_all()

    for name in os.listdir(COLLECTIONS_DIR):
        tar_path = os.path.join(COLLECTIONS_DIR, name)
        if os.path.isdir(tar_path):
            continue
        elif not tarfile.is_tarfile(tar_path):
            continue

        sha256_hash = get_file_hash(tar_path)

        with tarfile.open(tar_path, mode='r') as collection_tar:
            try:
                manifest_file = collection_tar.getmember('MANIFEST.json')
            except KeyError:
                continue

            with collection_tar.extractfile(manifest_file) as manifest_fd:
                b_manifest_json = manifest_fd.read()

            manifest = json.loads(b_manifest_json.decode('utf-8'))['collection_info']
            insert_collection(manifest, name, os.path.getsize(tar_path), sha256_hash)


def login_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth and auth != 'Token %s' % AUTH_TOKEN:
            return '{"detail":"Invalid token."}', 401, {'Content-Type': 'application/json'}

        return f(*args, **kwargs)
    return decorated


def login_reject(f):
    @wraps(f)
    def decorate(*args, **kwargs):
        if 'Authorization' in request.headers:
            return 'Unknown error', 500

        return f(*args, **kwargs)
    return decorate


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


def process_import(import_task, collection_path):
    """ Very basic collection validation. """
    import_task.messages.append({'level': 'INFO', 'message': 'Starting import: task_id=%s' % import_task.id,
                                 'time': datetime.datetime.now().isoformat()})

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
            'message': 'Import Task "%s" failed: %s' % (import_task.id, str(e)),
            'time': datetime.datetime.now().isoformat()
        }
        import_task.messages.append(msg)
    except Exception as e:
        import_task.state = 'failed'
        import_task.error_code = 'GALAXYUNKNOWN'
        import_task.error_msg = str(e)

        msg = {
            'level': 'ERROR',
            'message': 'Import Task "%s" failed: Unknown error when validating collection: %s'
                       % (import_task.id, str(e)),
            'time': datetime.datetime.now().isoformat(),
        }
        import_task.messages.append(msg)
    finally:
        import_task.finished_at = datetime.datetime.now()


@app.route('/api/')
@app.route('/api/automation-hub/')
@login_optional
def api():
    if request.path == '/api/automation-hub/':
        return json_response({'available_versions': {'v3': 'v3/'}})
    else:
        return json_response({
            'description': 'FALAXY REST API',
            'current_version': 'v1',
            'available_versions': {'v1': 'v1/', 'v2': 'v2/'},
            'server_version': '6.6.6',
            'version_name': "That's not amoosing",
            'team_members': [
                'Bovine University'
            ]
        })


@app.route('/api/custom/collections/<filename>')
@app.route('/api/automation-hub/custom/collections/<filename>')
@login_optional
def get_collection_download_redirect(filename):
    # Both Galaxy and AH redirect the URL to S3 which rejects the request if Authorization is set. This replicates that
    # behaviour by redirecting to /api/custom/collections-download/<filename>.
    return redirect("%sapi/custom/collections-download/%s" % (request.url_root, filename))


@app.route('/api/custom/collections-download/<filename>')
@login_reject
def get_collection_download(filename):
    file_path = os.path.join(COLLECTIONS_DIR, filename)
    if not os.path.exists(file_path):
        response = {
            'code': 'not_found',
            'message': "Artifact '%s' does not exist." % filename,
        }
        return json_response(response, code=404)

    return send_file(file_path, as_attachment=True)


@app.route('/api/custom/reset/', methods=['POST'])
@app.route('/api/automation-hub/custom/reset/', methods=['POST'])
def reset_cache():
    clear = not request.is_json or request.get_json().get('clear', True)
    start_up(clear=clear)
    return "", 200


@app.route('/api/v1/namespaces/')
@login_optional
def namespaces():
    return json_pagination_response([n.get_api_info() for n in Namespace.query.all()], 1, full_link=False)


@app.route('/api/v1/namespaces/<namespace_id>/')
@login_optional
def namespaces_id(namespace_id):
    namespace = Namespace.query.filter_by(id=namespace_id).first()
    if not namespace:
        return json_response({'detail': 'Not found.'}, code=404)

    return json_response(namespace.get_api_info())


@app.route('/api/<api_version>/collection-imports/<import_id>/')
@app.route('/api/automation-hub/<api_version>/imports/collections/<import_id>/')
@login_required
def collection_imports(api_version, import_id):
    import_task = IMPORT_TABLE.get(import_id, None)
    if not import_task:
        return json_not_found_response(api_version)

    return json_response(import_task.get_api_info(api_version))


@app.route('/api/<api_version>/collections/', methods=['GET'])
@app.route('/api/automation-hub/<api_version>/collections/', methods=['GET'])
@login_optional
def collections_get(api_version):
    return json_pagination_response([c.get_api_info(api_version) for c in Collection.query.all()], api_version,
                                    full_link=False)


@app.route('/api/<api_version>/collections/', methods=['POST'])
@app.route('/api/automation-hub/<api_version>/artifacts/collections/', methods=['POST'])
@login_required
def collections_post(api_version):
    # Flask does not seem to parse the form data properly, will need to do it manually.
    post_data = request.get_data()

    content_length = request.headers.get('Content-Length')
    content_type_header = request.headers.get('Content-Type')

    if not content_length or not content_type_header:
        return json_galaxy_error(api_version, 'invalid', 'Invalid input.')

    content_type, boundary = content_type_header.split(';')
    if content_type != 'multipart/form-data':
        return json_galaxy_error(api_version, 'unsupported media type',
                                 'Unsupported medial type "%s" in request.' % content_type_header, status=415)

    boundary = re.findall(r'boundary=([\x00-\x7f]*)', boundary)[0]  # Boundary can take in any 7-bit ASCII chars.
    if not boundary:
        return json_galaxy_error(api_version, 'parse_error',
                                 'Multipart form parse error - Invalid boundary in multipart: ')

    # The boundary start and end is defined by 2 hyphen, ignore that when splitting the form data.
    form_data = [process_form_data(v) for v in post_data.split(b'--' + boundary.encode('ascii')) if v and v != b'--']

    # Verify the expected hash is there
    if form_data[0][0] != 'form-data' or 'name' not in form_data[0][1] or form_data[0][1]['name'] != 'sha256':
        return json_galaxy_error(api_version, 'parse_error',
                                 'Multipart form parse error - Missing form-data with sha256 hash')
    expected_hash = form_data[0][2].decode('ascii')

    # Verify the file data is there
    if form_data[1][0] != 'file' or 'filename' not in form_data[1][1]:
        return json_galaxy_error(api_version, 'parse_error', 'Multipart form parse error - Missing file with filename')
    filename = form_data[1][1]['filename']

    # The actual collection bytes is preset after the first 2 newlines, read that and place it into a temporary file.
    b_collection_tar = form_data[1][2].split(b'\r\n', 2)[2]
    sha256 = hashlib.sha256()
    import_path = os.path.join(IMPORT_TMP, filename)
    with open(import_path, mode='wb') as import_fd:
        sha256.update(b_collection_tar)
        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            return json_galaxy_error(api_version, 'invalid', 'The expected hash did not match the actual hash.',
                                     'Invalid input.')

        import_fd.write(b_collection_tar)

    # Galaxy does a basic check to ensure the collection doesn't already exist before starting the async import.
    if not tarfile.is_tarfile(import_path):
        return json_galaxy_error(api_version, 'invalid', 'Invalid input.')

    with tarfile.open(import_path, mode='r') as collection_tar:
        try:
            manifest_tar_fd = collection_tar.getmember('MANIFEST.json')
        except KeyError:
            return json_galaxy_error(api_version, 'invalid', 'Invalid input no MANIFEST.json')

        with collection_tar.extractfile(manifest_tar_fd) as manifest_fd:
            b_manifest_json = manifest_fd.read()

        try:
            manifest = json.loads(b_manifest_json.decode('utf-8')).get('collection_info', {})
        except ValueError:
            return json_galaxy_error(api_version, 'invalid', 'Invalid MANIFEST.json')

        if 'namespace' not in manifest or 'name' not in manifest or 'version' not in manifest:
            return json_galaxy_error(api_version, 'invalid', 'Missing required fields in MANIFEST.json')

        # Galaxy validates the namespace based on the filename before starting the import process
        existing_collection = CollectionVersion.get_collection_version(manifest['namespace'], manifest['name'],
                                                                       manifest['version'])
        if existing_collection:
            os.remove(import_path)
            return json_galaxy_error(api_version, 'conflict.artifact_exists', 'Artifact already exists.', status=409)

    with IMPORT_LOCK:
        if api_version == 'v2':
            import_id = len(IMPORT_TABLE)
            import_uri = '%sapi/v2/collection-imports/%s/' % (request.host_url, import_id)
        else:
            import_id = str(uuid.uuid4())
            import_uri = '/api/automation-hub/v3/imports/collections/%s/' % import_id

        import_task = ImportTask(import_id)
        IMPORT_TABLE[str(import_id)] = import_task

    import_thread = threading.Thread(target=process_import, args=(import_task, import_path))
    import_thread.daemon = True
    import_thread.start()

    return json_response({'task': import_uri})


@app.route('/api/<api_version>/collections/<namespace>/<name>/')
@app.route('/api/automation-hub/<api_version>/collections/<namespace>/<name>/')
@login_optional
def collection_info(api_version, namespace, name):
    collection = Collection.get_collection(namespace, name)
    if not collection:
        return json_not_found_response(api_version)

    return json_response(collection.get_api_info(api_version))


@app.route('/api/<api_version>/collections/<namespace>/<name>/versions/')
@app.route('/api/automation-hub/<api_version>/collections/<namespace>/<name>/versions/')
@login_optional
def collection_versions(api_version, namespace, name):
    collection = Collection.get_collection(namespace, name)
    if not collection:
        return json_not_found_response(api_version)

    return json_pagination_response(collection.get_api_versions(api_version), api_version)


@app.route('/api/<api_version>/collections/<namespace>/<name>/versions/<version>/')
@app.route('/api/automation-hub/<api_version>/collections/<namespace>/<name>/versions/<version>/')
@login_optional
def collection_version(api_version, namespace, name, version):
    version_info = CollectionVersion.get_collection_version(namespace, name, version)
    if not version_info:
        return json_not_found_response(api_version)

    return json_response(version_info.get_api_info(api_version))


def main():
    start_up()

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

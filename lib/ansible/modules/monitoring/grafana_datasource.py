#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Thierry Sallé (@seuf)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: grafana_datasource
author:
  - Thierry Sallé (@seuf)
  - Martin Wang (@martinwangjian)
version_added: "2.5"
short_description: Manage Grafana datasources
description:
  - Create/update/delete Grafana datasources via API.
options:
  grafana_url:
    description:
      - The Grafana URL.
    required: true
  name:
    description:
      - The name of the datasource.
    required: true
  ds_type:
    description:
     - The type of the datasource.
    required: true
    choices: [ graphite, prometheus, elasticsearch, influxdb, opentsdb, mysql, postgres, cloudwatch, alexanderzobnin-zabbix-datasource]
  url:
    description:
      - The URL of the datasource.
    required: true
    aliases: [ ds_url ]
  access:
    description:
      - The access mode for this datasource.
    choices: [ direct, proxy ]
    default: proxy
  url_username:
    description:
      - The Grafana API user.
    default: admin
    aliases: [ grafana_user ]
    version_added: 2.7
  url_password:
    description:
      - The Grafana API password.
    default: admin
    aliases: [ grafana_password ]
    version_added: 2.7
  grafana_api_key:
    description:
      - The Grafana API key.
      - If set, C(grafana_user) and C(grafana_password) will be ignored.
  database:
    description:
      - Name of the database for the datasource.
      - This options is required when the C(ds_type) is C(influxdb), C(elasticsearch) (index name), C(mysql) or C(postgres).
    required: false
  user:
    description:
      - The datasource login user for influxdb datasources.
  password:
    description:
      - The datasource password
  basic_auth_user:
    description:
      - The datasource basic auth user.
      - Setting this option with basic_auth_password will enable basic auth.
  basic_auth_password:
    description:
      - The datasource basic auth password, when C(basic auth) is C(yes).
  with_credentials:
    description:
      - Whether credentials such as cookies or auth headers should be sent with cross-site requests.
    type: bool
    default: 'no'
  tls_client_cert:
    description:
      - The client TLS certificate.
      - If C(tls_client_cert) and C(tls_client_key) are set, this will enable TLS authentication.
      - Starts with ----- BEGIN CERTIFICATE -----
  tls_client_key:
    description:
      - The client TLS private key
      - Starts with ----- BEGIN RSA PRIVATE KEY -----
  tls_ca_cert:
    description:
      - The TLS CA certificate for self signed certificates.
      - Only used when C(tls_client_cert) and C(tls_client_key) are set.
  tls_skip_verify:
    description:
      - Skip the TLS datasource certificate verification.
    type: bool
    default: False
    version_added: 2.6
  is_default:
    description:
      - Make this datasource the default one.
    type: bool
    default: 'no'
  org_id:
    description:
      - Grafana Organisation ID in which the datasource should be created.
      - Not used when C(grafana_api_key) is set, because the C(grafana_api_key) only belong to one organisation.
    default: 1
  state:
    description:
      - Status of the datasource
    choices: [ absent, present ]
    default: present
  es_version:
    description:
      - Elasticsearch version (for C(ds_type = elasticsearch) only)
      - Version 56 is for elasticsearch 5.6+ where tou can specify the C(max_concurrent_shard_requests) option.
    choices: [ 2, 5, 56 ]
    default: 5
  max_concurrent_shard_requests:
    description:
      - Starting with elasticsearch 5.6, you can specify the max concurrent shard per requests.
    default: 256
  time_field:
    description:
      - Name of the time field in elasticsearch ds.
      - For example C(@timestamp)
    default: timestamp
  time_interval:
    description:
      - Minimum group by interval for C(influxdb) or C(elasticsearch) datasources.
      - for example C(>10s)
  interval:
    description:
      - For elasticsearch C(ds_type), this is the index pattern used.
    choices: ['', 'Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly']
  tsdb_version:
    description:
      - The opentsdb version.
      - Use C(1) for <=2.1, C(2) for ==2.2, C(3) for ==2.3.
    choices: [ 1, 2, 3 ]
    default: 1
  tsdb_resolution:
    description:
      - The opentsdb time resolution.
    choices: [ millisecond, second ]
    default: second
  sslmode:
    description:
      - SSL mode for C(postgres) datasource type.
    choices: [ disable, require, verify-ca, verify-full ]
  trends:
    required: false
    description:
      - Use trends or not for zabbix datasource type
    type: bool
    version_added: 2.6
  client_cert:
    required: false
    description:
      - TLS certificate path used by ansible to query grafana api
    version_added: 2.8
  client_key:
    required: false
    description:
      - TLS private key path used by ansible to query grafana api
    version_added: 2.8
  validate_certs:
    description:
      - Whether to validate the Grafana certificate.
    type: bool
    default: 'yes'
  use_proxy:
    description:
      - Boolean of whether or not to use proxy.
    default: 'yes'
    type: bool
    version_added: 2.8
  aws_auth_type:
    description:
      - Type for AWS authentication for CloudWatch datasource type (authType of grafana api)
    default: 'keys'
    choices: [ keys, credentials, arn ]
    version_added: 2.8
  aws_default_region:
    description:
      - AWS default region for CloudWatch datasource type
    default: 'us-east-1'
    choices: [
      ap-northeast-1, ap-northeast-2, ap-southeast-1, ap-southeast-2, ap-south-1,
      ca-central-1,
      cn-north-1, cn-northwest-1,
      eu-central-1, eu-west-1, eu-west-2, eu-west-3,
      sa-east-1,
      us-east-1, us-east-2, us-gov-west-1, us-west-1, us-west-2
    ]
    version_added: 2.8
  aws_credentials_profile:
    description:
      - Profile for AWS credentials for CloudWatch datasource type when C(aws_auth_type) is C(credentials)
    default: ''
    required: false
    version_added: 2.8
  aws_access_key:
    description:
      - AWS access key for CloudWatch datasource type when C(aws_auth_type) is C(keys)
    default: ''
    required: false
    version_added: 2.8
  aws_secret_key:
    description:
      - AWS secret key for CloudWatch datasource type when C(aws_auth_type) is C(keys)
    default: ''
    required: false
    version_added: 2.8
  aws_assume_role_arn:
    description:
      - AWS IAM role arn to assume for CloudWatch datasource type when C(aws_auth_type) is C(arn)
    default: ''
    required: false
    version_added: 2.8
  aws_custom_metrics_namespaces:
    description:
      - Namespaces of Custom Metrics for CloudWatch datasource type
    default: ''
    required: false
    version_added: 2.8

'''

EXAMPLES = '''
---
- name: Create elasticsearch datasource
  grafana_datasource:
    name: "datasource-elastic"
    grafana_url: "https://grafana.company.com"
    grafana_user: "admin"
    grafana_password: "xxxxxx"
    org_id: "1"
    ds_type: "elasticsearch"
    ds_url: "https://elastic.company.com:9200"
    database: "[logstash_]YYYY.MM.DD"
    basic_auth_user: "grafana"
    basic_auth_password: "******"
    time_field: "@timestamp"
    time_interval: "1m"
    interval: "Daily"
    es_version: 56
    max_concurrent_shard_requests: 42
    tls_ca_cert: "/etc/ssl/certs/ca.pem"

- name: Create influxdb datasource
  grafana_datasource:
    name: "datasource-influxdb"
    grafana_url: "https://grafana.company.com"
    grafana_user: "admin"
    grafana_password: "xxxxxx"
    org_id: "1"
    ds_type: "influxdb"
    ds_url: "https://influx.company.com:8086"
    database: "telegraf"
    time_interval: ">10s"
    tls_ca_cert: "/etc/ssl/certs/ca.pem"

- name: Create postgres datasource
  grafana_datasource:
    name: "datasource-postgres"
    grafana_url: "https://grafana.company.com"
    grafana_user: "admin"
    grafana_password: "xxxxxx"
    org_id: "1"
    ds_type: "postgres"
    ds_url: "postgres.company.com:5432"
    database: "db"
    user: "postgres"
    password: "iampgroot"
    sslmode: "verify-full"

- name: Create cloudwatch datasource
  grafana_datasource:
    name: "datasource-cloudwatch"
    grafana_url: "https://grafana.company.com"
    grafana_user: "admin"
    grafana_password: "xxxxxx"
    org_id: "1"
    ds_type: "cloudwatch"
    url: "http://monitoring.us-west-1.amazonaws.com"
    aws_auth_type: "keys"
    aws_default_region: "us-west-1"
    aws_access_key: "speakFriendAndEnter"
    aws_secret_key: "mel10n"
    aws_custom_metrics_namespaces: "n1,n2"
'''

RETURN = '''
---
name:
  description: name of the datasource created.
  returned: success
  type: str
  sample: test-ds
id:
  description: Id of the datasource
  returned: success
  type: int
  sample: 42
before:
  description: datasource returned by grafana api
  returned: changed
  type: dict
  sample: { "access": "proxy",
        "basicAuth": false,
        "database": "test_*",
        "id": 1035,
        "isDefault": false,
        "jsonData": {
            "esVersion": 5,
            "timeField": "@timestamp",
            "timeInterval": "1m",
        },
        "name": "grafana_datasource_test",
        "orgId": 1,
        "type": "elasticsearch",
        "url": "http://elastic.company.com:9200",
        "user": "",
        "password": "",
        "withCredentials": false }
after:
  description: datasource updated by module
  returned: changed
  type: dict
  sample: { "access": "proxy",
        "basicAuth": false,
        "database": "test_*",
        "id": 1035,
        "isDefault": false,
        "jsonData": {
            "esVersion": 5,
            "timeField": "@timestamp",
            "timeInterval": "10s",
        },
        "name": "grafana_datasource_test",
        "orgId": 1,
        "type": "elasticsearch",
        "url": "http://elastic.company.com:9200",
        "user": "",
        "password": "",
        "withCredentials": false }
'''

import json
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_text

__metaclass__ = type


class GrafanaAPIException(Exception):
    pass


def grafana_switch_organisation(module, grafana_url, org_id, headers):
    r, info = fetch_url(module, '%s/api/user/using/%d' % (grafana_url, org_id), headers=headers, method='POST')
    if info['status'] != 200:
        raise GrafanaAPIException('Unable to switch to organization %s : %s' % (org_id, info))


def grafana_headers(module, data):
    headers = {'content-type': 'application/json; charset=utf8'}
    if 'grafana_api_key' in data and data['grafana_api_key']:
        headers['Authorization'] = "Bearer %s" % data['grafana_api_key']
    else:
        module.params['force_basic_auth'] = True
        grafana_switch_organisation(module, data['grafana_url'], data['org_id'], headers)

    return headers


def grafana_datasource_exists(module, grafana_url, name, headers):
    datasource_exists = False
    ds = {}
    r, info = fetch_url(module, '%s/api/datasources/name/%s' % (grafana_url, quote(name)), headers=headers, method='GET')
    if info['status'] == 200:
        datasource_exists = True
        ds = json.loads(to_text(r.read(), errors='surrogate_or_strict'))
    elif info['status'] == 404:
        datasource_exists = False
    else:
        raise GrafanaAPIException('Unable to get datasource %s : %s' % (name, info))

    return datasource_exists, ds


def grafana_create_datasource(module, data):

    # define data payload for grafana API
    payload = {'orgId': data['org_id'],
               'name': data['name'],
               'type': data['ds_type'],
               'access': data['access'],
               'url': data['url'],
               'database': data['database'],
               'withCredentials': data['with_credentials'],
               'isDefault': data['is_default'],
               'user': data['user'],
               'password': data['password']}

    # define basic auth
    if 'basic_auth_user' in data and data['basic_auth_user'] and 'basic_auth_password' in data and data['basic_auth_password']:
        payload['basicAuth'] = True
        payload['basicAuthUser'] = data['basic_auth_user']
        payload['basicAuthPassword'] = data['basic_auth_password']
    else:
        payload['basicAuth'] = False

    # define tls auth
    json_data = {}
    if data.get('tls_client_cert') and data.get('tls_client_key'):
        json_data['tlsAuth'] = True
        if data.get('tls_ca_cert'):
            payload['secureJsonData'] = {
                'tlsCACert': data['tls_ca_cert'],
                'tlsClientCert': data['tls_client_cert'],
                'tlsClientKey': data['tls_client_key']
            }
            json_data['tlsAuthWithCACert'] = True
        else:
            payload['secureJsonData'] = {
                'tlsClientCert': data['tls_client_cert'],
                'tlsClientKey': data['tls_client_key']
            }
    else:
        json_data['tlsAuth'] = False
        json_data['tlsAuthWithCACert'] = False
        if data.get('tls_ca_cert'):
            payload['secureJsonData'] = {
                'tlsCACert': data['tls_ca_cert']
            }

    if data.get('tls_skip_verify'):
        json_data['tlsSkipVerify'] = True

    # datasource type related parameters
    if data['ds_type'] == 'elasticsearch':
        json_data['esVersion'] = data['es_version']
        json_data['timeField'] = data['time_field']
        if data.get('interval'):
            json_data['interval'] = data['interval']
        if data['es_version'] >= 56:
            json_data['maxConcurrentShardRequests'] = data['max_concurrent_shard_requests']

    if data['ds_type'] == 'elasticsearch' or data['ds_type'] == 'influxdb':
        if data.get('time_interval'):
            json_data['timeInterval'] = data['time_interval']

    if data['ds_type'] == 'opentsdb':
        json_data['tsdbVersion'] = data['tsdb_version']
        if data['tsdb_resolution'] == 'second':
            json_data['tsdbResolution'] = 1
        else:
            json_data['tsdbResolution'] = 2

    if data['ds_type'] == 'postgres':
        json_data['sslmode'] = data['sslmode']
        if data.get('password'):
            payload['secureJsonData'] = {'password': data.get('password')}

    if data['ds_type'] == 'alexanderzobnin-zabbix-datasource':
        if data.get('trends'):
            json_data['trends'] = True

    if data['ds_type'] == 'cloudwatch':
        if data.get('aws_credentials_profle'):
            payload['database'] = data.get('aws_credentials_profile')

        json_data['authType'] = data['aws_auth_type']
        json_data['defaultRegion'] = data['aws_default_region']

        if data.get('aws_custom_metrics_namespaces'):
            json_data['customMetricsNamespaces'] = data.get('aws_custom_metrics_namespaces')
        if data.get('aws_assume_role_arn'):
            json_data['assumeRoleArn'] = data.get('aws_assume_role_arn')
        if data.get('aws_access_key') and data.get('aws_secret_key'):
            payload['secureJsonData'] = {'accessKey': data.get('aws_access_key'), 'secretKey': data.get('aws_secret_key')}

    payload['jsonData'] = json_data

    # define http header
    headers = grafana_headers(module, data)

    # test if datasource already exists
    datasource_exists, ds = grafana_datasource_exists(module, data['grafana_url'], data['name'], headers=headers)

    result = {}
    if datasource_exists is True:
        del ds['typeLogoUrl']
        if ds.get('version'):
            del ds['version']
        if ds.get('readOnly'):
            del ds['readOnly']
        if ds['basicAuth'] is False:
            del ds['basicAuthUser']
            del ds['basicAuthPassword']
        if 'jsonData' in ds:
            if 'tlsAuth' in ds['jsonData'] and ds['jsonData']['tlsAuth'] is False:
                del ds['secureJsonFields']
            if 'tlsAuth' not in ds['jsonData']:
                del ds['secureJsonFields']
        payload['id'] = ds['id']
        if ds == payload:
            # unchanged
            result['name'] = data['name']
            result['id'] = ds['id']
            result['msg'] = "Datasource %s unchanged." % data['name']
            result['changed'] = False
        else:
            # update
            r, info = fetch_url(module, '%s/api/datasources/%d' % (data['grafana_url'], ds['id']), data=json.dumps(payload), headers=headers, method='PUT')
            if info['status'] == 200:
                res = json.loads(to_text(r.read(), errors='surrogate_or_strict'))
                result['name'] = data['name']
                result['id'] = ds['id']
                result['before'] = ds
                result['after'] = payload
                result['msg'] = "Datasource %s updated %s" % (data['name'], res['message'])
                result['changed'] = True
            else:
                raise GrafanaAPIException('Unable to update the datasource id %d : %s' % (ds['id'], info))
    else:
        # create
        r, info = fetch_url(module, '%s/api/datasources' % data['grafana_url'], data=json.dumps(payload), headers=headers, method='POST')
        if info['status'] == 200:
            res = json.loads(to_text(r.read(), errors='surrogate_or_strict'))
            result['msg'] = "Datasource %s created : %s" % (data['name'], res['message'])
            result['changed'] = True
            result['name'] = data['name']
            result['id'] = res['id']
        else:
            raise GrafanaAPIException('Unable to create the new datasource %s : %s - %s.' % (data['name'], info['status'], info))

    return result


def grafana_delete_datasource(module, data):

    headers = grafana_headers(module, data)

    # test if datasource already exists
    datasource_exists, ds = grafana_datasource_exists(module, data['grafana_url'], data['name'], headers=headers)

    result = {}
    if datasource_exists is True:
        # delete
        r, info = fetch_url(module, '%s/api/datasources/name/%s' % (data['grafana_url'], quote(data['name'])), headers=headers, method='DELETE')
        if info['status'] == 200:
            res = json.loads(to_text(r.read(), errors='surrogate_or_strict'))
            result['msg'] = "Datasource %s deleted : %s" % (data['name'], res['message'])
            result['changed'] = True
            result['name'] = data['name']
            result['id'] = 0
        else:
            raise GrafanaAPIException('Unable to update the datasource id %s : %s' % (ds['id'], info))
    else:
        # datasource does not exist, do nothing
        result = {'msg': "Datasource %s does not exist." % data['name'],
                  'changed': False,
                  'id': 0,
                  'name': data['name']}

    return result


def main():
    # use the predefined argument spec for url
    argument_spec = url_argument_spec()
    # remove unnecessary arguments
    del argument_spec['force']
    del argument_spec['force_basic_auth']
    del argument_spec['http_agent']

    argument_spec.update(
        name=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'],
                   default='present'),
        grafana_url=dict(type='str', required=True),
        url_username=dict(aliases=['grafana_user'], default='admin'),
        url_password=dict(aliases=['grafana_password'], default='admin', no_log=True),
        ds_type=dict(choices=['graphite',
                              'prometheus',
                              'elasticsearch',
                              'influxdb',
                              'opentsdb',
                              'mysql',
                              'postgres',
                              'cloudwatch',
                              'alexanderzobnin-zabbix-datasource']),
        url=dict(required=True, type='str', aliases=['ds_url']),
        access=dict(default='proxy', choices=['proxy', 'direct']),
        grafana_api_key=dict(type='str', no_log=True),
        database=dict(type='str'),
        user=dict(default='', type='str'),
        password=dict(default='', no_log=True, type='str'),
        basic_auth_user=dict(type='str'),
        basic_auth_password=dict(type='str', no_log=True),
        with_credentials=dict(default=False, type='bool'),
        tls_client_cert=dict(type='str', no_log=True),
        tls_client_key=dict(type='str', no_log=True),
        tls_ca_cert=dict(type='str', no_log=True),
        tls_skip_verify=dict(type='bool', default=False),
        is_default=dict(default=False, type='bool'),
        org_id=dict(default=1, type='int'),
        es_version=dict(type='int', default=5, choices=[2, 5, 56]),
        max_concurrent_shard_requests=dict(type='int', default=256),
        time_field=dict(default='@timestamp', type='str'),
        time_interval=dict(type='str'),
        interval=dict(type='str', choices=['', 'Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly'], default=''),
        tsdb_version=dict(type='int', default=1, choices=[1, 2, 3]),
        tsdb_resolution=dict(type='str', default='second', choices=['second', 'millisecond']),
        sslmode=dict(default='disable', choices=['disable', 'require', 'verify-ca', 'verify-full']),
        trends=dict(default=False, type='bool'),
        aws_auth_type=dict(default='keys', choices=['keys', 'credentials', 'arn']),
        aws_default_region=dict(default='us-east-1', choices=['ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2', 'ap-south-1',
                                                              'ca-central-1',
                                                              'cn-north-1', 'cn-northwest-1',
                                                              'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
                                                              'sa-east-1',
                                                              'us-east-1', 'us-east-2', 'us-gov-west-1', 'us-west-1', 'us-west-2']),
        aws_access_key=dict(default='', no_log=True, type='str'),
        aws_secret_key=dict(default='', no_log=True, type='str'),
        aws_credentials_profile=dict(default='', type='str'),
        aws_assume_role_arn=dict(default='', type='str'),
        aws_custom_metrics_namespaces=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[['url_username', 'url_password', 'org_id'], ['tls_client_cert', 'tls_client_key']],
        mutually_exclusive=[['url_username', 'grafana_api_key'], ['tls_ca_cert', 'tls_skip_verify']],
        required_if=[
            ['ds_type', 'opentsdb', ['tsdb_version', 'tsdb_resolution']],
            ['ds_type', 'influxdb', ['database']],
            ['ds_type', 'elasticsearch', ['database', 'es_version', 'time_field', 'interval']],
            ['ds_type', 'mysql', ['database']],
            ['ds_type', 'postgres', ['database', 'sslmode']],
            ['ds_type', 'cloudwatch', ['aws_auth_type', 'aws_default_region']],
            ['es_version', 56, ['max_concurrent_shard_requests']]
        ],
    )

    try:
        if module.params['state'] == 'present':
            result = grafana_create_datasource(module, module.params)
        else:
            result = grafana_delete_datasource(module, module.params)
    except GrafanaAPIException as e:
        module.fail_json(
            failed=True,
            msg="error %s : %s " % (type(e), e)
        )
        return

    module.exit_json(
        failed=False,
        **result
    )
    return


if __name__ == '__main__':
    main()

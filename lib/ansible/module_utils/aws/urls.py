# Copyright: (c) 2018, Aaron Haaf <aabonh@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import hashlib
import hmac
import operator

from ansible.module_utils.urls import open_url
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, HAS_BOTO3
from ansible.module_utils.six.moves.urllib.parse import urlencode
from boto3 import session

def hexdigest(s):
    """
    Returns the sha256 hexdigest of a string after encoding.
    """

    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def format_querystring(params=None):
    """
    Returns properly url-encoded query string from the provided params dict.

    It's specially sorted for cannonical requests
    """

    if not params:
        return ""

    # Query string values must be URL-encoded (space=%20). The parameters must be sorted by name.
    return urlencode(sorted(params.items(), operator.itemgetter(0)))


# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    '''
    Return digest for key applied to msg
    '''

    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(key, dateStamp, regionName, serviceName):
    '''
    Returns signature key for AWS resource
    '''

    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


def get_aws_key_pair(module):
    '''
    Returns aws_access_key_id, aws_secret_access_key for a module.

    Prefers the credentials from a profile over inline'd keys
    '''

    if not HAS_BOTO3:
        module.fail_json("get_aws_key_pair requires boto3")

    dummy, dummy, boto_params = get_aws_connection_info(module, boto3=True)

    profile = boto_params.get('profile_name')

    if profile:
        s = session.Session(profile_name=profile)
        credentials = s.get_credentials()
        return credentials.access_key, credentials.secret_key
    else:
        return boto_params.get('aws_access_key_id'), boto_params.get('aws_secret_access_key')


# Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
def signed_request(method="GET", service=None, host=None, uri=None, query=None, body="", module=None, headers=None):
    """Generate a SigV4 request to an AWS resource for a module

    This is used if you wish to authenticate with AWS credentials to a secure endpoint like an elastisearch domain.

    Returns :class:`HTTPResponse` object.

    Example:
        result = signed_request(
            module=this,
            service="es",
            host="search-recipes1-xxxxxxxxx.us-west-2.es.amazonaws.com",
        )

    :kwarg host: endpoint to talk to
    :kwarg service: AWS id of service (like `ec2` or `es`)
    :kwarg module: An AnsibleAWSModule to gather connection info from

    :kwarg body: (optional) Payload to send
    :kwarg method: (optional) HTTP verb to use
    :kwarg query: (optional) dict of query params to handle
    :kwarg uri: (optional) Resource path without query parameters
    :returns: HTTPResponse
    """

    if not HAS_BOTO3:
        module.fail_json("A sigv4 signed_request requires boto3")

    # "Constants"

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope
    algorithm = 'AWS4-HMAC-SHA256'

    # AWS stuff

    region, dummy, dummy = get_aws_connection_info(module, boto3=True)
    access_key, secret_key = get_aws_key_pair(module)

    if not access_key:
        module.fail_json(msg="aws_access_key_id is missing")
    if not secret_key:
        module.fail_json(msg="aws_secret_access_key is missing")

    credential_scope = '/'.join([datestamp, region, service, 'aws4_request'])

    # Argument Defaults

    uri = uri or "/"
    query_string = format_querystring(query) if query else ""

    headers = headers or dict()
    query = query or dict()

    headers.update({
        "host": host,
        'x-amz-date': amz_date,
    })

    if method is "GET":
        body = ""

    body = body

    # Derived data

    body_hash = hexdigest(body)
    signed_headers = ";".join(sorted(headers.keys()))

    # Setup Cannonical request to generate auth token

    cannonical_headers = "\n".join([
        key.lower().strip() + ":" + value for key, value in headers.items()
    ]) + '\n'  # Note additional trailing newline

    cannonical_request = "\n".join([
        method,
        uri,
        query_string,
        cannonical_headers,
        signed_headers,
        body_hash,
    ])

    string_to_sign = '\n'.join([algorithm, amz_date, credential_scope, hexdigest(cannonical_request)])

    # Sign the Cannonical request

    signing_key = get_signature_key(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Make auth header with that info

    authorization_header = "{0} Credential={1}/{2}, SignedHeaders={3}, Signature={4}".format(
        algorithm, access_key, credential_scope, signed_headers, signature
    )

    # PERFORM THE REQUEST!

    url = "https://" + host + uri

    if query_string is not "":
        url = url + "?" + query_string

    final_headers = {
        'x-amz-date': amz_date,
        'Authorization': authorization_header,
    }

    final_headers.update(headers)

    return open_url(url, method=method, data=body, headers=final_headers)

# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by the calling module

HAS_MD5 = True
try:
    from hashlib import md5
except ImportError:
    try:
        from md5 import md5
    except ImportError:
        HAS_MD5 = False

S3_EXTRA_ARGS = {
    'acl': 'ACL',
    'cachecontrol': 'CacheControl',
    'contentdisposition': 'ContentDisposition',
    'contentencoding': 'ContentEncoding',
    'contentlanguage': 'ContentLanguage',
    'contenttype': 'ContentType',
    'expires': 'Expires',
    'grantfullcontrol': 'GrantFullControl',
    'grantread': 'GrantRead',
    'grantreadacp': 'GrantReadACP',
    'grantwriteacp': 'GrantWriteACP',
    'metadata': 'Metadata',
    'requestpayer': 'RequestPayer',
    'serversideencryption': 'ServerSideEncryption',
    'storageclass': 'StorageClass',
    'ssecustomeralgorithm': 'SSECustomerAlgorithm',
    'ssecustomerkey': 'SSECustomerKey',
    'ssecustomerkeymd5': 'SSECustomerKeyMD5',
    'ssekmskeyid': 'SSEKMSKeyId',
    'websiteredirectlocation': 'WebsiteRedirectLocation'
}


def calculate_etag(module, filename, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        digests = []

        s3_kwargs = dict(
            Bucket=bucket,
            Key=obj,
        )
        if version:
            s3_kwargs['VersionId'] = version

        with open(filename, 'rb') as f:
            for part_num in range(1, parts + 1):
                s3_kwargs['PartNumber'] = part_num
                try:
                    head = s3.head_object(**s3_kwargs)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to get head object")
                digests.append(md5(f.read(int(head['ContentLength']))))

        digest_squared = md5(b''.join(m.digest() for m in digests))
        return '"{0}-{1}"'.format(digest_squared.hexdigest(), len(digests))
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(module.md5(filename))


def dict_to_s3_extra_args(metadata):
    ret = {}

    for option in metadata:
        mangled = option.translate(None, '-_').lower()
        if mangled in S3_EXTRA_ARGS:
            ret[S3_EXTRA_ARGS[mangled]] = metadata[option]
        else:
            if 'Metadata' not in ret:
                ret['Metadata'] = {}
            ret['Metadata'][option] = metadata[option]

    return ret

def get_ec2_creds(module):

    # Check module args for credentials, then check environment vars

    ec2_url = module.params.get('ec2_url')
    ec2_secret_key = module.params.get('ec2_secret_key')
    ec2_access_key = module.params.get('ec2_access_key')
    region = module.params.get('region')

    if not ec2_url:
        if 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']
        elif 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']

    if not ec2_access_key:
        if 'EC2_ACCESS_KEY' in os.environ:
            ec2_access_key = os.environ['EC2_ACCESS_KEY']
        elif 'AWS_ACCESS_KEY_ID' in os.environ:
            ec2_access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif 'AWS_ACCESS_KEY' in os.environ:
            ec2_access_key = os.environ['AWS_ACCESS_KEY']

    if not ec2_secret_key:
        if 'EC2_SECRET_KEY' in os.environ:
            ec2_secret_key = os.environ['EC2_SECRET_KEY']
        elif 'AWS_SECRET_ACCESS_KEY' in os.environ:
            ec2_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif 'AWS_SECRET_KEY' in os.environ:
            ec2_secret_key = os.environ['AWS_SECRET_KEY']

    if not region:
        if 'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']
        elif 'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']

    return ec2_url, ec2_access_key, ec2_secret_key, region

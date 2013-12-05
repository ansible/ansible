def get_state_instances(ec2, instance_ids, state):
    """
    Retrieves instances which are in a given state
    """
    instances = []
    for res in ec2.get_all_instances(instance_ids=instance_ids, \
                                         filters={'instance-state-name':state}):
        for inst in res.instances:
            if inst.state == state:
                instances.append(get_instance_info(inst))
    return instances

def wait_for_instances(ec2, instance_ids, state, module, force_wait=False):
    wait = module.params.get('wait')
    if force_wait:
        wait = force_wait
    wait_timeout = int(module.params.get('wait_timeout'))
    num_counted = 0
    wait_timeout = time.time() + wait_timeout

    instances = []
    while wait_timeout > time.time() and num_counted < len(instance_ids):
        instances = get_state_instances(ec2, instance_ids, state)
        num_counted = len(instances)

        if not wait:
            break
        if num_counted < len(instance_ids):
            time.sleep(5)

    # waiting took too long
    if wait and wait_timeout < time.time() and num_stopped < len(instance_ids):
        module.fail_json(msg = "wait for instance stop timeout on %s" % time.asctime())

    return instances

def get_instance_info(inst):
    """
    Retrieves instance information from an instance
    ID and returns it as a dictionary
    """
    instance_info = {'id': inst.id,
                     'ami_launch_index': inst.ami_launch_index,
                     'private_ip': inst.private_ip_address,
                     'private_dns_name': inst.private_dns_name,
                     'public_ip': inst.ip_address,
                     'dns_name': inst.dns_name,
                     'public_dns_name': inst.public_dns_name,
                     'state_code': inst.state_code,
                     'architecture': inst.architecture,
                     'image_id': inst.image_id,
                     'key_name': inst.key_name,
                     'placement': inst.placement,
                     'kernel': inst.kernel,
                     'ramdisk': inst.ramdisk,
                     'launch_time': inst.launch_time,
                     'instance_type': inst.instance_type,
                     'root_device_type': inst.root_device_type,
                     'root_device_name': inst.root_device_name,
                     'state': inst.state,
                     'hypervisor': inst.hypervisor}
    try:
        instance_info['virtualization_type'] = getattr(inst,'virtualization_type')
    except AttributeError:
        instance_info['virtualization_type'] = None

    return instance_info

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

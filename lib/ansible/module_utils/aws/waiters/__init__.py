# extra waiters for AWS utils
from ansible.module_utils.aws.waiters import ec2 as ec2_waiters


def get_waiter(client, waiter_name):
    if client.__class__.__name__ == 'EC2':
        try:
            return ec2_waiters.waiters_by_name[waiter_name](client)
        except KeyError:
            raise NotImplementedError("Waiter {0} could not be found for client {1}. Available waiters: {2}".format(
                waiter_name, type(client), ', '.join(ec2_waiters.waiters_by_name.keys())))

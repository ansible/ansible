# (c) 2019 Piotr Wojciechowski (@wojciechowskipiotr) <piotr@it-playground.pl>
# (c) Thierry Bouvet (@tbouvet)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils._text import to_native


def get_swarm_node_id(client):
    """
    Returns the 'NodeID' of the Swarm node or 'None' if host is not in Swarm
    :param client: connection to client as AnsibleDockerClient object
    :return:
        NodeID of 'client' or 'None' if not part of Swarm
    """

    try:
        info = client.info()
    except APIError as exc:
        client.fail(msg="Failed to get node information for %s" % to_native(exc))

    if info:
        json_str = json.dumps(info, ensure_ascii=False)
        swarm_info = json.loads(json_str)
        if swarm_info['Swarm']['NodeID']:
            return swarm_info['Swarm']['NodeID']
    return None


def check_if_swarm_node(client, node_id=None):
    """
    Checking if host is part of Docker Swarm. If 'node_id' is not provided it reads the Docker host
    system information looking if specific key in output exists. If 'node_id' is provided then it tries to
    read node information assuming it is run on Swarm manager. The get_node_info() method handles exception if
    it is not executed on Swarm manager

    :param client: connection to client as AnsibleDockerClient object
    :param node_id: Node identifier
    :return:
        bool: True if node is part of Swarm, False otherwise
    """

    if node_id is None:
        try:
            info = client.info()
        except APIError:
            client.fail(msg="Failed to get host information.")

        if info:
            json_str = json.dumps(info, ensure_ascii=False)
            swarm_info = json.loads(json_str)
            if swarm_info['Swarm']['NodeID']:
                return True
        return False
    else:
        try:
            node_info = get_node_info(client, node_id)
        except APIError:
            return

        if node_info['ID'] is not None:
            return True
        return False


def check_if_swarm_manager(client):
    """
    Checks if client role is set as Manager in Swarm. The client is the docker host on which module action
    is performed. The inspect_swarm() will fail if node is not a manager

    :param client: connection to client as AnsibleDockerClient object
    :return: True if node is Swarm Manager, False otherwise
    """

    try:
        client.inspect_swarm()
        return True
    except APIError:
        return False


def check_if_swarm_worker(client):
    """
    Checks if client role is set as Worker in Swarm. The client is the docker host on which module action
    is performed.

    :param client: connection to client as AnsibleDockerClient object
    :return: True if node is Swarm Worker, False otherwise
    """

    if check_if_swarm_node(client) and not check_if_swarm_manager(client):
        return True
    return False


def get_node_info(client, node_id=None):
    """
    Returns Swarm node info as in 'docker node inspect' command or fail the playbook in case of errors

    :param client: connection to client as AnsibleDockerClient object
    :param node_id: node ID, if None then method will try to get node_id of 'client'
    :return:
        Node information structure
    """

    if node_id is None:
        node_id = get_swarm_node_id(client)

    if node_id is None:
        client.fail(msg="Failed to get node information.")

    try:
        node_info = client.inspect_node(node_id=node_id)
    except APIError as exc:
        raise exc
    json_str = json.dumps(node_info, ensure_ascii=False)
    node_info = json.loads(json_str)
    return node_info

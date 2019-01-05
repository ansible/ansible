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
from ansible.module_utils.docker_common import AnsibleDockerClient


class AnsibleDockerSwarmClient(AnsibleDockerClient):

    def __init__(self, **kwargs):
        super(AnsibleDockerSwarmClient, self).__init__(**kwargs)

    def get_swarm_node_id(self):
        """
        Get the 'NodeID' of the Swarm node or 'None' if host is not in Swarm. It returns the NodeID
        of Docker host the module is executed on
        :return:
            NodeID of host or 'None' if not part of Swarm
        """

        try:
            info = self.info()
        except APIError as exc:
            self.fail(msg="Failed to get node information for %s" % to_native(exc))

        if info:
            json_str = json.dumps(info, ensure_ascii=False)
            swarm_info = json.loads(json_str)
            if swarm_info['Swarm']['NodeID']:
                return swarm_info['Swarm']['NodeID']
        return None

    def check_if_swarm_node(self, node_id=None):
        """
        Checking if host is part of Docker Swarm. If 'node_id' is not provided it reads the Docker host
        system information looking if specific key in output exists. If 'node_id' is provided then it tries to
        read node information assuming it is run on Swarm manager. The get_node_info() method handles exception if
        it is not executed on Swarm manager

        :param node_id: Node identifier
        :return:
            bool: True if node is part of Swarm, False otherwise
        """

        if node_id is None:
            try:
                info = self.info()
            except APIError:
                self.fail(msg="Failed to get host information.")

            if info:
                json_str = json.dumps(info, ensure_ascii=False)
                swarm_info = json.loads(json_str)
                if swarm_info['Swarm']['NodeID']:
                    return True
            return False
        else:
            try:
                node_info = self.get_node_info(node_id)
            except APIError:
                return

            if node_info['ID'] is not None:
                return True
            return False

    def check_if_swarm_manager(self):
        """
        Checks if node role is set as Manager in Swarm. The node is the docker host on which module action
        is performed. The inspect_swarm() will fail if node is not a manager

        :return: True if node is Swarm Manager, False otherwise
        """

        try:
            self.inspect_swarm()
            return True
        except APIError:
            return False

    def check_if_swarm_worker(self):
        """
        Checks if node role is set as Worker in Swarm. The node is the docker host on which module action
        is performed. Will fail if run on host that is not part of Swarm via check_if_swarm_node()

        :return: True if node is Swarm Worker, False otherwise
        """

        if self.check_if_swarm_node() and not self.check_if_swarm_manager():
            return True
        return False

    def check_if_swarm_node_is_down(self, node_id=None):
        """
        Checks if node status on Swarm manager is 'down'. If node_id is provided it query manager about
        node specified in parameter, otherwise it query manager itself. If run on Swarm Worker node or
        host that is not part of Swarm it will fail the playbook

        :param node_id: node ID or name, if None then method will try to get node_id of host module run on
        :return:
            True if node is part of swarm but its state is down, False otherwise
        """

        if node_id is None:
            node_info = self.get_node_info()
        else:
            node_info = self.get_node_info(node_id=node_id)
        if node_info['Status']['State'] == 'down':
            return True
        return False

    def get_node_info(self, node_id=None):
        """
        Returns Swarm node info as in 'docker node inspect' command or fail the playbook in case of errors

        :param node_id: node ID or name, if None then method will try to get node_id of host module run on
        :return:
            Node information structure
        """

        if node_id is None:
            node_id = self.get_swarm_node_id()

        if node_id is None:
            self.fail(msg="Failed to get node information.")

        try:
            node_info = self.inspect_node(node_id=node_id)
        except APIError as exc:
            raise exc
        json_str = json.dumps(node_info, ensure_ascii=False)
        node_info = json.loads(json_str)
        return node_info

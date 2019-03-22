# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.

HAS_SF_SDK = False
try:
    import solidfire.common

    HAS_SF_SDK = True
except Exception:
    HAS_SF_SDK = False


def has_sf_sdk():
    return HAS_SF_SDK


class NaElementSWModule(object):

    def __init__(self, elem):
        self.elem_connect = elem
        self.parameters = dict()

    def get_volume(self, volume_id):
        """
            Return volume details if volume exists for given volume_id

            :param volume_id: volume ID
            :type volume_id: int
            :return: Volume dict if found, None if not found
            :rtype: dict
        """
        volume_list = self.elem_connect.list_volumes(volume_ids=[volume_id])
        for volume in volume_list.volumes:
            if volume.volume_id == volume_id:
                if str(volume.delete_time) == "":
                    return volume
        return None

    def get_volume_id(self, vol_name, account_id):
        """
            Return volume id from the given (valid) account_id if found
            Return None if not found

            :param vol_name: Name of the volume
            :type vol_name: str
            :param account_id: Account ID
            :type account_id: int

            :return: Volume ID of the first matching volume if found. None if not found.
            :rtype: int
        """
        volume_list = self.elem_connect.list_volumes_for_account(account_id=account_id)
        for volume in volume_list.volumes:
            if volume.name == vol_name:
                # return volume_id
                if str(volume.delete_time) == "":
                    return volume.volume_id
        return None

    def volume_id_exists(self, volume_id):
        """
            Return volume_id if volume exists for given volume_id

            :param volume_id: volume ID
            :type volume_id: int
            :return: Volume ID if found, None if not found
            :rtype: int
        """
        volume_list = self.elem_connect.list_volumes(volume_ids=[volume_id])
        for volume in volume_list.volumes:
            if volume.volume_id == volume_id:
                if str(volume.delete_time) == "":
                    return volume.volume_id
        return None

    def volume_exists(self, volume, account_id):
        """
            Return volume_id if exists, None if not found

            :param volume: Volume ID or Name
            :type volume: str
            :param account_id: Account ID (valid)
            :type account_id: int
            :return: Volume ID if found, None if not found
        """
        # If volume is an integer, get_by_id
        if str(volume).isdigit():
            volume_id = int(volume)
            try:
                if self.volume_id_exists(volume_id):
                    return volume_id
            except solidfire.common.ApiServerError:
                # don't fail, continue and try get_by_name
                pass
        # get volume by name
        volume_id = self.get_volume_id(volume, account_id)
        return volume_id

    def get_snapshot(self, snapshot_id, volume_id):
        """
            Return snapshot details if found

            :param snapshot_id: Snapshot ID or Name
            :type snapshot_id: str
            :param volume_id: Account ID (valid)
            :type volume_id: int
            :return: Snapshot dict if found, None if not found
            :rtype: dict
        """
        # mandate src_volume_id although not needed by sdk
        snapshot_list = self.elem_connect.list_snapshots(
            volume_id=volume_id)
        for snapshot in snapshot_list.snapshots:
            # if actual id is provided
            if str(snapshot_id).isdigit() and snapshot.snapshot_id == int(snapshot_id):
                return snapshot
            # if snapshot name is provided
            elif snapshot.name == snapshot_id:
                return snapshot
        return None

    def account_exists(self, account):
        """
            Return account_id if account exists for given account id or name
            Raises an exception if account does not exist

            :param account: Account ID or Name
            :type account: str
            :return: Account ID if found, None if not found
        """
        # If account is an integer, get_by_id
        if account.isdigit():
            account_id = int(account)
            try:
                result = self.elem_connect.get_account_by_id(account_id=account_id)
                if result.account.account_id == account_id:
                    return account_id
            except solidfire.common.ApiServerError:
                # don't fail, continue and try get_by_name
                pass
        # get account by name, the method returns an Exception if account doesn't exist
        result = self.elem_connect.get_account_by_name(username=account)
        return result.account.account_id

    def set_element_attributes(self, source):
        """
            Return telemetry attributes for the current execution

            :param source: name of the module
            :type source: str
            :return: a dict containing telemetry attributes
        """
        attributes = {}
        attributes['config-mgmt'] = 'ansible'
        attributes['event-source'] = source
        return(attributes)

from ansible.modules.cloud.amazon import redshift_cross_region_snapshots as rcrs

mock_status_enabled = {
    'SnapshotCopyGrantName': 'snapshot-us-east-1-to-us-west-2',
    'DestinationRegion': 'us-west-2',
    'RetentionPeriod': 1,
}

mock_status_disabled = {}

mock_request_illegal = {
    'snapshot_copy_grant': 'changed',
    'destination_region': 'us-west-2',
    'snapshot_retention_period': 1
}

mock_request_update = {
    'snapshot_copy_grant': 'snapshot-us-east-1-to-us-west-2',
    'destination_region': 'us-west-2',
    'snapshot_retention_period': 3
}

mock_request_no_update = {
    'snapshot_copy_grant': 'snapshot-us-east-1-to-us-west-2',
    'destination_region': 'us-west-2',
    'snapshot_retention_period': 1
}


def test_fail_at_unsupported_operations():
    response = rcrs.requesting_unsupported_modifications(
        mock_status_enabled, mock_request_illegal
    )
    assert response is True


def test_needs_update_true():
    response = rcrs.needs_update(mock_status_enabled, mock_request_update)
    assert response is True


def test_no_change():
    response = rcrs.requesting_unsupported_modifications(
        mock_status_enabled, mock_request_no_update
    )
    needs_update_response = rcrs.needs_update(mock_status_enabled, mock_request_no_update)
    assert response is False
    assert needs_update_response is False

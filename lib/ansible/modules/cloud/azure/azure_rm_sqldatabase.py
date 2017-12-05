#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_sqldatabase
version_added: "2.5"
short_description: Manage Database instance
description:
    - Create, update and delete instance of Database

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    name:
        description:
            - The name of the database to be operated on (updated or created).
        required: True
    tags:
        description:
            - Resource tags.
    location:
        description:
            - Resource location.
    collation:
        description:
            - The collation of the database. If createMode is not Default, this value is ignored.
    create_mode:
        description:
            - "Specifies the mode of database creation.\n\nDefault: regular database creation.\n\nCopy: creates a database as a copy of an existing database.
                sourceDatabaseId must be specified as the resource ID of the source database.\n\nOnlineSecondary/NonReadableSecondary: creates a database as
               a (readable or nonreadable) secondary replica of an existing database. sourceDatabaseId must be specified as the resource ID of the existing p
               rimary database.\n\nPointInTimeRestore: Creates a database by restoring a point in time backup of an existing database. sourceDatabaseId must
               be specified as the resource ID of the existing database, and restorePointInTime must be specified.\n\nRecovery: Creates a database by restori
               ng a geo-replicated backup. sourceDatabaseId must be specified as the recoverable database resource ID to restore.\n\nRestore: Creates a datab
               ase by restoring a backup of a deleted database. sourceDatabaseId must be specified. If sourceDatabaseId is the database's original resource I
               D, then sourceDatabaseDeletionDate must be specified. Otherwise sourceDatabaseId must be the restorable dropped database resource ID and sourc
               eDatabaseDeletionDate is ignored. restorePointInTime may also be specified to restore from an earlier point in time.\n\nRestoreLongTermRetenti
               onBackup: Creates a database by restoring from a long term retention vault. recoveryServicesRecoveryPointResourceId must be specified as the r
               ecovery point resource ID.\n\nCopy, NonReadableSecondary, OnlineSecondary and RestoreLongTermRetentionBackup are not supported for DataWarehou
               se edition. Possible values include: 'Copy', 'Default', 'NonReadableSecondary', 'OnlineSecondary', 'PointInTimeRestore', 'Recovery', 'Restore'
               , 'RestoreLongTermRetentionBackup'"
    source_database_id:
        description:
            - "Conditional. If createMode is Copy, NonReadableSecondary, OnlineSecondary, PointInTimeRestore, Recovery, or Restore, then this value is requir
               ed. Specifies the resource ID of the source database. If createMode is NonReadableSecondary or OnlineSecondary, the name of the source databas
               e must be the same as the new database being created."
    source_database_deletion_date:
        description:
            - "Conditional. If createMode is Restore and sourceDatabaseId is the deleted database's original resource id when it existed (as opposed to its c
               urrent restorable dropped database id), then this value is required. Specifies the time that the database was deleted."
    restore_point_in_time:
        description:
            - "Conditional. If createMode is PointInTimeRestore, this value is required. If createMode is Restore, this value is optional. Specifies the poin
               t in time (ISO8601 format) of the source database that will be restored to create the new database. Must be greater than or equal to the sourc
               e database's earliestRestoreDate value."
    recovery_services_recovery_point_resource_id:
        description:
            - "Conditional. If createMode is RestoreLongTermRetentionBackup, then this value is required. Specifies the resource ID of the recovery point to
               restore from."
    edition:
        description:
            - "The edition of the database. The DatabaseEditions enumeration contains all the valid editions. If createMode is NonReadableSecondary or Online
               Secondary, this value is ignored. To see possible values, query the capabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/
               locations/{locationID}/capabilities) referred to by operationId: 'Capabilities_ListByLocation.'. Possible values include: 'Web', 'Business', '
               Basic', 'Standard', 'Premium', 'Free', 'Stretch', 'DataWarehouse', 'System', 'System2'"
    max_size_bytes:
        description:
            - "The max size of the database expressed in bytes. If createMode is not Default, this value is ignored. To see possible values, query the capabi
               lities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId: 'Capabili
               ties_ListByLocation.'"
    requested_service_objective_id:
        description:
            - "The configured service level objective ID of the database. This is the service level objective that is in the process of being applied to the
               database. Once successfully updated, it will match the value of currentServiceObjectiveId property. If requestedServiceObjectiveId and request
               edServiceObjectiveName are both updated, the value of requestedServiceObjectiveId overrides the value of requestedServiceObjectiveName. To see
                possible values, query the capabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) ref
               erred to by operationId: 'Capabilities_ListByLocation.'"
    requested_service_objective_name:
        description:
            - "The name of the configured service level objective of the database. This is the service level objective that is in the process of being applie
               d to the database. Once successfully updated, it will match the value of serviceLevelObjective property. To see possible values, query the cap
               abilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId: 'Capab
               ilities_ListByLocation.'. Possible values include: 'Basic', 'S0', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3', 'P4', 'P6', 'P11', 'P15', 'System', 'Sys
               tem2', 'ElasticPool'"
    elastic_pool_name:
        description:
            - "The name of the elastic pool the database is in. If elasticPoolName and requestedServiceObjectiveName are both updated, the value of requested
               ServiceObjectiveName is ignored. Not supported for DataWarehouse edition."
    read_scale:
        description:
            - "Conditional. If the database is a geo-secondary, readScale indicates whether read-only connections are allowed to this database or not. Not su
               pported for DataWarehouse edition. Possible values include: 'Enabled', 'Disabled'"
    sample_name:
        description:
            - "Indicates the name of the sample schema to apply when creating this database. If createMode is not Default, this value is ignored. Not support
               ed for DataWarehouse edition. Possible values include: 'AdventureWorksLT'"
    zone_redundant:
        description:
            - Whether or not this database is zone redundant, which means the replicas of this database will be spread across multiple availability zones.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) Database
    azure_rm_sqldatabase:
      resource_group: resource_group_name
      server_name: server_name
      name: database_name
      tags: tags
      location: location
      collation: collation
      create_mode: create_mode
      source_database_id: source_database_id
      source_database_deletion_date: source_database_deletion_date
      restore_point_in_time: restore_point_in_time
      recovery_services_recovery_point_resource_id: recovery_services_recovery_point_resource_id
      edition: edition
      max_size_bytes: max_size_bytes
      requested_service_objective_id: requested_service_objective_id
      requested_service_objective_name: requested_service_objective_name
      elastic_pool_name: elastic_pool_name
      read_scale: read_scale
      sample_name: sample_name
      zone_redundant: zone_redundant
'''

RETURN = '''
state:
    description: Current state of Database
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: id
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: name
        type:
            description:
                - Resource type.
            returned: always
            type: str
            sample: type
        tags:
            description:
                - Resource tags.
            returned: always
            type: complex
            sample: tags
        location:
            description:
                - Resource location.
            returned: always
            type: str
            sample: location
        kind:
            description:
                - Kind of database.  This is metadata used for the Azure portal experience.
            returned: always
            type: str
            sample: kind
        collation:
            description:
                - The collation of the database. If createMode is not Default, this value is ignored.
            returned: always
            type: str
            sample: collation
        creation_date:
            description:
                - The creation date of the database (ISO8601 format).
            returned: always
            type: datetime
            sample: creation_date
        containment_state:
            description:
                - The containment state of the database.
            returned: always
            type: long
            sample: containment_state
        current_service_objective_id:
            description:
                - The current service level objective ID of the database. This is the ID of the service level objective that is currently active.
            returned: always
            type: str
            sample: current_service_objective_id
        database_id:
            description:
                - The ID of the database.
            returned: always
            type: str
            sample: database_id
        earliest_restore_date:
            description:
                - This records the earliest start date and time that restore is available for this database (ISO8601 format).
            returned: always
            type: datetime
            sample: earliest_restore_date
        create_mode:
            description:
                - "Specifies the mode of database creation.\n\nDefault: regular database creation.\n\nCopy: creates a database as a copy of an existing datab
                   ase. sourceDatabaseId must be specified as the resource ID of the source database.\n\nOnlineSecondary/NonReadableSecondary: creates a data
                   base as a (readable or nonreadable) secondary replica of an existing database. sourceDatabaseId must be specified as the resource ID of th
                   e existing primary database.\n\nPointInTimeRestore: Creates a database by restoring a point in time backup of an existing database. source
                   DatabaseId must be specified as the resource ID of the existing database, and restorePointInTime must be specified.\n\nRecovery: Creates a
                    database by restoring a geo-replicated backup. sourceDatabaseId must be specified as the recoverable database resource ID to restore.\n\n
                   Restore: Creates a database by restoring a backup of a deleted database. sourceDatabaseId must be specified. If sourceDatabaseId is the da
                   tabase's original resource ID, then sourceDatabaseDeletionDate must be specified. Otherwise sourceDatabaseId must be the restorable droppe
                   d database resource ID and sourceDatabaseDeletionDate is ignored. restorePointInTime may also be specified to restore from an earlier poin
                   t in time.\n\nRestoreLongTermRetentionBackup: Creates a database by restoring from a long term retention vault. recoveryServicesRecoveryPo
                   intResourceId must be specified as the recovery point resource ID.\n\nCopy, NonReadableSecondary, OnlineSecondary and RestoreLongTermReten
                   tionBackup are not supported for DataWarehouse edition. Possible values include: 'Copy', 'Default', 'NonReadableSecondary', 'OnlineSeconda
                   ry', 'PointInTimeRestore', 'Recovery', 'Restore', 'RestoreLongTermRetentionBackup'"
            returned: always
            type: str
            sample: create_mode
        source_database_id:
            description:
                - "Conditional. If createMode is Copy, NonReadableSecondary, OnlineSecondary, PointInTimeRestore, Recovery, or Restore, then this value is re
                   quired. Specifies the resource ID of the source database. If createMode is NonReadableSecondary or OnlineSecondary, the name of the source
                    database must be the same as the new database being created."
            returned: always
            type: str
            sample: source_database_id
        source_database_deletion_date:
            description:
                - "Conditional. If createMode is Restore and sourceDatabaseId is the deleted database's original resource id when it existed (as opposed to i
                   ts current restorable dropped database id), then this value is required. Specifies the time that the database was deleted."
            returned: always
            type: datetime
            sample: source_database_deletion_date
        restore_point_in_time:
            description:
                - "Conditional. If createMode is PointInTimeRestore, this value is required. If createMode is Restore, this value is optional. Specifies the
                   point in time (ISO8601 format) of the source database that will be restored to create the new database. Must be greater than or equal to t
                   he source database's earliestRestoreDate value."
            returned: always
            type: datetime
            sample: restore_point_in_time
        recovery_services_recovery_point_resource_id:
            description:
                - "Conditional. If createMode is RestoreLongTermRetentionBackup, then this value is required. Specifies the resource ID of the recovery point
                    to restore from."
            returned: always
            type: str
            sample: recovery_services_recovery_point_resource_id
        edition:
            description:
                - "The edition of the database. The DatabaseEditions enumeration contains all the valid editions. If createMode is NonReadableSecondary or On
                   lineSecondary, this value is ignored. To see possible values, query the capabilities API (/subscriptions/{subscriptionId}/providers/Micros
                   oft.Sql/locations/{locationID}/capabilities) referred to by operationId: 'Capabilities_ListByLocation.'. Possible values include: 'Web', '
                   Business', 'Basic', 'Standard', 'Premium', 'Free', 'Stretch', 'DataWarehouse', 'System', 'System2'"
            returned: always
            type: str
            sample: edition
        max_size_bytes:
            description:
                - "The max size of the database expressed in bytes. If createMode is not Default, this value is ignored. To see possible values, query the ca
                   pabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId: '
                   Capabilities_ListByLocation.'"
            returned: always
            type: str
            sample: max_size_bytes
        requested_service_objective_id:
            description:
                - "The configured service level objective ID of the database. This is the service level objective that is in the process of being applied to
                   the database. Once successfully updated, it will match the value of currentServiceObjectiveId property. If requestedServiceObjectiveId and
                    requestedServiceObjectiveName are both updated, the value of requestedServiceObjectiveId overrides the value of requestedServiceObjective
                   Name. To see possible values, query the capabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/c
                   apabilities) referred to by operationId: 'Capabilities_ListByLocation.'"
            returned: always
            type: str
            sample: requested_service_objective_id
        requested_service_objective_name:
            description:
                - "The name of the configured service level objective of the database. This is the service level objective that is in the process of being ap
                   plied to the database. Once successfully updated, it will match the value of serviceLevelObjective property. To see possible values, query
                    the capabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operati
                   onId: 'Capabilities_ListByLocation.'. Possible values include: 'Basic', 'S0', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3', 'P4', 'P6', 'P11', 'P15'
                   , 'System', 'System2', 'ElasticPool'"
            returned: always
            type: str
            sample: requested_service_objective_name
        service_level_objective:
            description:
                - "The current service level objective of the database. Possible values include: 'Basic', 'S0', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3', 'P4', 'P6
                   ', 'P11', 'P15', 'System', 'System2', 'ElasticPool'"
            returned: always
            type: str
            sample: service_level_objective
        status:
            description:
                - The status of the database.
            returned: always
            type: str
            sample: status
        elastic_pool_name:
            description:
                - "The name of the elastic pool the database is in. If elasticPoolName and requestedServiceObjectiveName are both updated, the value of reque
                   stedServiceObjectiveName is ignored. Not supported for DataWarehouse edition."
            returned: always
            type: str
            sample: elastic_pool_name
        default_secondary_location:
            description:
                - The default secondary region for this database.
            returned: always
            type: str
            sample: default_secondary_location
        service_tier_advisors:
            description:
                - The list of service tier advisors for this database. Expanded property
            returned: always
            type: complex
            sample: service_tier_advisors
            suboptions:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: id
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: name
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: type
                observation_period_start:
                    description:
                        - The observation period start (ISO8601 format).
                    returned: always
                    type: datetime
                    sample: observation_period_start
                observation_period_end:
                    description:
                        - The observation period start (ISO8601 format).
                    returned: always
                    type: datetime
                    sample: observation_period_end
                active_time_ratio:
                    description:
                        - The activeTimeRatio for service tier advisor.
                    returned: always
                    type: float
                    sample: active_time_ratio
                min_dtu:
                    description:
                        - Gets or sets minDtu for service tier advisor.
                    returned: always
                    type: float
                    sample: min_dtu
                avg_dtu:
                    description:
                        - Gets or sets avgDtu for service tier advisor.
                    returned: always
                    type: float
                    sample: avg_dtu
                max_dtu:
                    description:
                        - Gets or sets maxDtu for service tier advisor.
                    returned: always
                    type: float
                    sample: max_dtu
                max_size_in_gb:
                    description:
                        - Gets or sets maxSizeInGB for service tier advisor.
                    returned: always
                    type: float
                    sample: max_size_in_gb
                service_level_objective_usage_metrics:
                    description:
                        - Gets or sets serviceLevelObjectiveUsageMetrics for the service tier advisor.
                    returned: always
                    type: complex
                    sample: service_level_objective_usage_metrics
                    suboptions:
                        service_level_objective:
                            description:
                                - "The serviceLevelObjective for SLO usage metric. Possible values include: 'Basic', 'S0', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3'
                                   , 'P4', 'P6', 'P11', 'P15', 'System', 'System2', 'ElasticPool'"
                            returned: always
                            type: str
                            sample: service_level_objective
                        service_level_objective_id:
                            description:
                                - The serviceLevelObjectiveId for SLO usage metric.
                            returned: always
                            type: str
                            sample: service_level_objective_id
                        in_range_time_ratio:
                            description:
                                - Gets or sets inRangeTimeRatio for SLO usage metric.
                            returned: always
                            type: float
                            sample: in_range_time_ratio
                current_service_level_objective:
                    description:
                        - Gets or sets currentServiceLevelObjective for service tier advisor.
                    returned: always
                    type: str
                    sample: current_service_level_objective
                current_service_level_objective_id:
                    description:
                        - Gets or sets currentServiceLevelObjectiveId for service tier advisor.
                    returned: always
                    type: str
                    sample: current_service_level_objective_id
                usage_based_recommendation_service_level_objective:
                    description:
                        - Gets or sets usageBasedRecommendationServiceLevelObjective for service tier advisor.
                    returned: always
                    type: str
                    sample: usage_based_recommendation_service_level_objective
                usage_based_recommendation_service_level_objective_id:
                    description:
                        - Gets or sets usageBasedRecommendationServiceLevelObjectiveId for service tier advisor.
                    returned: always
                    type: str
                    sample: usage_based_recommendation_service_level_objective_id
                database_size_based_recommendation_service_level_objective:
                    description:
                        - Gets or sets databaseSizeBasedRecommendationServiceLevelObjective for service tier advisor.
                    returned: always
                    type: str
                    sample: database_size_based_recommendation_service_level_objective
                database_size_based_recommendation_service_level_objective_id:
                    description:
                        - Gets or sets databaseSizeBasedRecommendationServiceLevelObjectiveId for service tier advisor.
                    returned: always
                    type: str
                    sample: database_size_based_recommendation_service_level_objective_id
                disaster_plan_based_recommendation_service_level_objective:
                    description:
                        - Gets or sets disasterPlanBasedRecommendationServiceLevelObjective for service tier advisor.
                    returned: always
                    type: str
                    sample: disaster_plan_based_recommendation_service_level_objective
                disaster_plan_based_recommendation_service_level_objective_id:
                    description:
                        - Gets or sets disasterPlanBasedRecommendationServiceLevelObjectiveId for service tier advisor.
                    returned: always
                    type: str
                    sample: disaster_plan_based_recommendation_service_level_objective_id
                overall_recommendation_service_level_objective:
                    description:
                        - Gets or sets overallRecommendationServiceLevelObjective for service tier advisor.
                    returned: always
                    type: str
                    sample: overall_recommendation_service_level_objective
                overall_recommendation_service_level_objective_id:
                    description:
                        - Gets or sets overallRecommendationServiceLevelObjectiveId for service tier advisor.
                    returned: always
                    type: str
                    sample: overall_recommendation_service_level_objective_id
                confidence:
                    description:
                        - Gets or sets confidence for service tier advisor.
                    returned: always
                    type: float
                    sample: confidence
        transparent_data_encryption:
            description:
                - The transparent data encryption info for this database.
            returned: always
            type: complex
            sample: transparent_data_encryption
            suboptions:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: id
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: name
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: type
                location:
                    description:
                        - Resource location.
                    returned: always
                    type: str
                    sample: location
                status:
                    description:
                        - "The status of the database transparent data encryption. Possible values include: 'Enabled', 'Disabled'"
                    returned: always
                    type: str
                    sample: status
        recommended_index:
            description:
                - The recommended indices for this database.
            returned: always
            type: complex
            sample: recommended_index
            suboptions:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: id
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: name
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: type
                action:
                    description:
                        - "The proposed index action. You can create a missing index, drop an unused index, or rebuild an existing index to improve its perfo
                           rmance. Possible values include: 'Create', 'Drop', 'Rebuild'"
                    returned: always
                    type: str
                    sample: action
                state:
                    description:
                        - "The current recommendation state. Possible values include: 'Active', 'Pending', 'Executing', 'Verifying', 'Pending Revert', 'Rever
                           ting', 'Reverted', 'Ignored', 'Expired', 'Blocked', 'Success'"
                    returned: always
                    type: str
                    sample: state
                created:
                    description:
                        - The UTC datetime showing when this resource was created (ISO8601 format).
                    returned: always
                    type: datetime
                    sample: created
                last_modified:
                    description:
                        - The UTC datetime of when was this resource last changed (ISO8601 format).
                    returned: always
                    type: datetime
                    sample: last_modified
                index_type:
                    description:
                        - "The type of index (CLUSTERED, NONCLUSTERED, COLUMNSTORE, CLUSTERED COLUMNSTORE). Possible values include: 'CLUSTERED', 'NONCLUSTER
                           ED', 'COLUMNSTORE', 'CLUSTERED COLUMNSTORE'"
                    returned: always
                    type: str
                    sample: index_type
                schema:
                    description:
                        - The schema where table to build index over resides
                    returned: always
                    type: str
                    sample: schema
                table:
                    description:
                        - The table on which to build index.
                    returned: always
                    type: str
                    sample: table
                columns:
                    description:
                        - Columns over which to build index
                    returned: always
                    type: str
                    sample: columns
                included_columns:
                    description:
                        - The list of column names to be included in the index
                    returned: always
                    type: str
                    sample: included_columns
                index_script:
                    description:
                        - The full build index script
                    returned: always
                    type: str
                    sample: index_script
                estimated_impact:
                    description:
                        - The estimated impact of doing recommended index action.
                    returned: always
                    type: complex
                    sample: estimated_impact
                    suboptions:
                        name:
                            description:
                                - The name of the impact dimension.
                            returned: always
                            type: str
                            sample: name
                        unit:
                            description:
                                - The unit in which estimated impact to dimension is measured.
                            returned: always
                            type: str
                            sample: unit
                        change_value_absolute:
                            description:
                                - The absolute impact to dimension.
                            returned: always
                            type: float
                            sample: change_value_absolute
                        change_value_relative:
                            description:
                                - The relative impact to dimension (null if not applicable)
                            returned: always
                            type: float
                            sample: change_value_relative
                reported_impact:
                    description:
                        - The values reported after index action is complete.
                    returned: always
                    type: complex
                    sample: reported_impact
                    suboptions:
                        name:
                            description:
                                - The name of the impact dimension.
                            returned: always
                            type: str
                            sample: name
                        unit:
                            description:
                                - The unit in which estimated impact to dimension is measured.
                            returned: always
                            type: str
                            sample: unit
                        change_value_absolute:
                            description:
                                - The absolute impact to dimension.
                            returned: always
                            type: float
                            sample: change_value_absolute
                        change_value_relative:
                            description:
                                - The relative impact to dimension (null if not applicable)
                            returned: always
                            type: float
                            sample: change_value_relative
        failover_group_id:
            description:
                - The resource identifier of the failover group containing this database.
            returned: always
            type: str
            sample: failover_group_id
        read_scale:
            description:
                - "Conditional. If the database is a geo-secondary, readScale indicates whether read-only connections are allowed to this database or not. No
                   t supported for DataWarehouse edition. Possible values include: 'Enabled', 'Disabled'"
            returned: always
            type: str
            sample: read_scale
        sample_name:
            description:
                - "Indicates the name of the sample schema to apply when creating this database. If createMode is not Default, this value is ignored. Not sup
                   ported for DataWarehouse edition. Possible values include: 'AdventureWorksLT'"
            returned: always
            type: str
            sample: sample_name
        zone_redundant:
            description:
                - Whether or not this database is zone redundant, which means the replicas of this database will be spread across multiple availability zones.
            returned: always
            type: str
            sample: zone_redundant
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDatabases(AzureRMModuleBase):
    """Configuration class for an Azure RM Database resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            server_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            tags=dict(
                type='dict',
                required=False
            ),
            location=dict(
                type='str',
                required=False
            ),
            collation=dict(
                type='str',
                required=False
            ),
            create_mode=dict(
                type='str',
                required=False
            ),
            source_database_id=dict(
                type='str',
                required=False
            ),
            source_database_deletion_date=dict(
                type='datetime',
                required=False
            ),
            restore_point_in_time=dict(
                type='datetime',
                required=False
            ),
            recovery_services_recovery_point_resource_id=dict(
                type='str',
                required=False
            ),
            edition=dict(
                type='str',
                required=False
            ),
            max_size_bytes=dict(
                type='str',
                required=False
            ),
            requested_service_objective_id=dict(
                type='str',
                required=False
            ),
            requested_service_objective_name=dict(
                type='str',
                required=False
            ),
            elastic_pool_name=dict(
                type='str',
                required=False
            ),
            read_scale=dict(
                type='str',
                required=False
            ),
            sample_name=dict(
                type='str',
                required=False
            ),
            zone_redundant=dict(
                type='str',
                required=False
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.server_name = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False, state=dict())
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMDatabases, self).__init__(derived_arg_spec=self.module_arg_spec,
                                               supports_check_mode=True,
                                               supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif key == "tags":
                self.parameters["tags"] = kwargs[key]
            elif key == "location":
                self.parameters["location"] = kwargs[key]
            elif key == "collation":
                self.parameters["collation"] = kwargs[key]
            elif key == "create_mode":
                self.parameters["create_mode"] = kwargs[key]
            elif key == "source_database_id":
                self.parameters["source_database_id"] = kwargs[key]
            elif key == "source_database_deletion_date":
                self.parameters["source_database_deletion_date"] = kwargs[key]
            elif key == "restore_point_in_time":
                self.parameters["restore_point_in_time"] = kwargs[key]
            elif key == "recovery_services_recovery_point_resource_id":
                self.parameters["recovery_services_recovery_point_resource_id"] = kwargs[key]
            elif key == "edition":
                self.parameters["edition"] = kwargs[key]
            elif key == "max_size_bytes":
                self.parameters["max_size_bytes"] = kwargs[key]
            elif key == "requested_service_objective_id":
                self.parameters["requested_service_objective_id"] = kwargs[key]
            elif key == "requested_service_objective_name":
                self.parameters["requested_service_objective_name"] = kwargs[key]
            elif key == "elastic_pool_name":
                self.parameters["elastic_pool_name"] = kwargs[key]
            elif key == "read_scale":
                self.parameters["read_scale"] = kwargs[key]
            elif key == "sample_name":
                self.parameters["sample_name"] = kwargs[key]
            elif key == "zone_redundant":
                self.parameters["zone_redundant"] = kwargs[key]

        old_response = None
        results = dict()

        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {0} not found'.format(self.resource_group))

        if not ("location" in self.parameters):
            self.parameters["location"] = resource_group.location

        old_response = self.get_database()

        if not old_response:
            self.log("Database instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Database instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Database instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Database instance")

            if self.check_mode:
                return self.results

            self.results['state'] = self.create_update_database()
            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(self.results['state'])

            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Database instance deleted")
            self.delete_database()
            self.results['changed'] = True
        else:
            self.log("Database instance unchanged")
            self.results['state'] = old_response
            self.results['changed'] = False

        return self.results

    def create_update_database(self):
        '''
        Creates or updates Database with the specified configuration.

        :return: deserialized Database instance state dictionary
        '''
        self.log("Creating / Updating the Database instance {0}".format(self.name))

        try:
            response = self.mgmt_client.databases.create_or_update(self.resource_group,
                                                                   self.server_name,
                                                                   self.name,
                                                                   self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Database instance.')
            self.fail("Error creating the Database instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_database(self):
        '''
        Deletes specified Database instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Database instance {0}".format(self.name))
        try:
            response = self.mgmt_client.databases.delete(self.resource_group,
                                                         self.server_name,
                                                         self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Database instance.')
            self.fail("Error deleting the Database instance: {0}".format(str(e)))

        return True

    def get_database(self):
        '''
        Gets the properties of the specified Database.

        :return: deserialized Database instance state dictionary
        '''
        self.log("Checking if the Database instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.databases.get(self.resource_group,
                                                      self.server_name,
                                                      self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Database instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Database instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMDatabases()

if __name__ == '__main__':
    main()

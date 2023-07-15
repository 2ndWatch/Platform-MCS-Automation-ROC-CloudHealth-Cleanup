import botocore.exceptions
import os
import shutil


def get_db_snapshot(rds_client, snapshot_id, logger):
    error_msg = f'      {snapshot_id} is not an RDS snapshot in this region or account.'
    logger.info(f'   Searching for {snapshot_id}...')
    db_snapshot_exists = False

    try:
        response = rds_client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)
        if response['DBSnapshots']:
            logger.info('      RDS snapshot found.')
            db_snapshot_exists = True
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)

    return db_snapshot_exists


def get_cluster_snapshot(rds_client, snapshot_id, logger):
    error_msg = f'      {snapshot_id} is not an Aurora snapshot in this region or account.'
    logger.info(f'   Searching for {snapshot_id}...')
    cluster_snapshot_exists = False

    try:
        response = rds_client.describe_db_cluster_snapshots(DBClusterSnapshotIdentifier=snapshot_id)
        if response['DBClusterSnapshots']:
            logger.info('      Aurora snapshot found.')
            cluster_snapshot_exists = True
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)

    return cluster_snapshot_exists


def delete_db_snapshot(rds_client, snapshot_id, dry_run, logger):
    logger.info(f'   Trying deletion of {snapshot_id}...')
    deleted = False
    if dry_run:
        logger.info('      Dry Run is set to True. There is no DryRun parameter for this API call. This message means '
                    'some other logic failed and the API call was prevented here instead.')
    else:
        try:
            response = rds_client.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)
            logger.info(f'      {response}')
            deleted = True
        except botocore.exceptions.ClientError as e:
            logger.info(f'      {e}')

    return deleted


def delete_cluster_snapshot(rds_client, snapshot_id, dry_run, logger):
    logger.info(f'   Trying deletion of {snapshot_id}...')
    deleted = False
    if dry_run:
        logger.info('      Dry Run is set to True. There is no DryRun parameter for this API call. This message means '
                    'some other logic failed and the API call was prevented here instead.')
    else:
        try:
            response = rds_client.delete_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot_id)
            logger.info(f'      {response}')
            deleted = True
        except botocore.exceptions.ClientError as e:
            logger.info(f'      {e}')

    return deleted


def delete_snapshots(rds_client, client_name, region_name, resource_name, dry_run, run_date_time, logger):
    resource_ids_file_name = f'{client_name} {resource_name}.txt'
    deleted_ids_file_name = f'{client_name} {resource_name} deleted.txt'
    snapshots_deleted = 0

    # Copy the resource ids file if a copy doesn't already exist
    file_copy_path = f'{client_name}_{run_date_time}/Copy of {resource_ids_file_name}'
    if not os.path.isfile(file_copy_path):
        shutil.copy(f'{client_name}_{run_date_time}/{resource_ids_file_name}', file_copy_path)
        logger.info('Initial copy of resource ID file was successful.')

    # Read snapshots from file
    try:
        with open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'r') as file:
            snapshots_list = [line.strip() for line in file]
            logger.info(f'Locating {len(snapshots_list)} snapshots...')
    except FileNotFoundError:
        logger.info(f'File not found: {resource_ids_file_name}. Skipping snapshot deletion in {region_name}.')
        return snapshots_deleted

    original_snapshots_list_length = len(snapshots_list)
    rds_snapshots_to_delete = []
    aurora_snapshots_to_delete = []

    # Search for each snapshot. If it exists, delete the snapshot
    for snap in snapshots_list:
        if get_db_snapshot(rds_client, snap, logger):
            rds_snapshots_to_delete.append(snap)
        elif get_cluster_snapshot(rds_client, snap, logger):
            aurora_snapshots_to_delete.append(snap)
        else:
            logger.info(f'         Skipping {snap}...')

    # Double failsafe in place to prevent API calls if dry_run is set to True
    if dry_run:
        logger.info(f'\n\nDry Run is set to True. There is no DryRun parameter for delete_db_snapshot or '
                    f'delete_cluster_snapshot, so no API calls will be made in order to prevent resource deletion.'
                    f'\nThere are {len(rds_snapshots_to_delete)} RDS snapshots and {len(aurora_snapshots_to_delete)} '
                    f'Aurora snapshots that can be deleted in this region.')
        if rds_snapshots_to_delete:
            for snap_to_delete in rds_snapshots_to_delete:
                snapshots_list.remove(snap_to_delete)
        if aurora_snapshots_to_delete:
            for snap_to_delete in aurora_snapshots_to_delete:
                snapshots_list.remove(snap_to_delete)
    else:
        if rds_snapshots_to_delete:
            logger.info(f'\nDeleting {len(rds_snapshots_to_delete)} RDS snapshots...')
            file = open(f'{client_name}_{run_date_time}/{deleted_ids_file_name}', 'a')
            for snap_to_delete in rds_snapshots_to_delete:
                if delete_db_snapshot(rds_client, snap_to_delete, dry_run, logger):
                    snapshots_deleted += 1
                    file.write(snap_to_delete + '\n')
                    snapshots_list.remove(snap_to_delete)
            file.close()
        if aurora_snapshots_to_delete:
            logger.info(f'\nDeleting {len(aurora_snapshots_to_delete)} Aurora snapshots...')
            file = open(f'{client_name}_{run_date_time}/{deleted_ids_file_name}', 'a')
            for snap_to_delete in aurora_snapshots_to_delete:
                if delete_cluster_snapshot(rds_client, snap_to_delete, dry_run, logger):
                    snapshots_deleted += 1
                    file.write(snap_to_delete + '\n')
                    snapshots_list.remove(snap_to_delete)
            file.close()

    logger.info(f'\nNumber of snapshots deleted: {snapshots_deleted}')
    logger.info(f'Number of remaining snapshots: {len(snapshots_list)}')

    # Rewrite snapshots file if snapshots were deleted
    if 0 < len(snapshots_list) < original_snapshots_list_length:
        logger.info('Rewriting working snapshots file...')
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        file = open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'w')
        for snap in snapshots_list:
            file.write(snap + '\n')
        file.close()
    elif not snapshots_list:
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        if dry_run:
            logger.info('No snapshots deleted, but all snapshots were found. Snapshots file removed.')
        else:
            logger.info('All snapshots deleted. Snapshots file removed.')

    return snapshots_deleted

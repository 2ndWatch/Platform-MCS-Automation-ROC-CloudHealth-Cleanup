import botocore.exceptions
import os
import shutil


def get_snapshot(ec2_client, snapshot_id, logger):
    error_msg = f'      The snapshot {snapshot_id} does not exist in this region or account.'
    logger.info(f'   Searching for {snapshot_id}...')
    snapshot_exists = False

    try:
        response = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])
        if response['Snapshots']:
            logger.info('      Snapshot found.')
            snapshot_exists = True
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)

    return snapshot_exists


def delete_snapshot(ec2_client, snapshot_id, dry_run, logger):
    logger.info(f'   Trying deletion of {snapshot_id}...')
    deleted = False
    try:
        response = ec2_client.delete_snapshot(SnapshotId=snapshot_id, DryRun=dry_run)
        logger.info(f'      {response}')
        deleted = True
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        if 'DryRunOperation' in str(e):
            deleted = True

    return deleted


def delete_snapshots(ec2_client, client_name, region_name, resource_name, dry_run, run_date_time, logger):
    resource_ids_file_name = f'{client_name} {resource_name}.txt'
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
    snapshots_to_delete = []

    # Search for each snapshot. If it exists, delete the snapshot
    for snap in snapshots_list:
        if get_snapshot(ec2_client, snap, logger):
            snapshots_to_delete.append(snap)
    if snapshots_to_delete:
        logger.info(f'\nDeleting {len(snapshots_to_delete)} volumes...')
        for snap_to_delete in snapshots_to_delete:
            if delete_snapshot(ec2_client, snap_to_delete, dry_run, logger):
                snapshots_deleted += 1
                snapshots_list.remove(snap_to_delete)

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
        logger.info('All snapshots deleted. Snapshots file removed.')

    return snapshots_deleted

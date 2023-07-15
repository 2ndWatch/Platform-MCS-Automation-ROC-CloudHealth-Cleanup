import botocore.exceptions
import os
import shutil


def get_volume(ec2_client, volume_id, logger):
    error_msg = f'      The volume {volume_id} does not exist in this region or account.'
    logger.info(f'   Searching for {volume_id}...')
    volume_exists = False

    try:
        response = ec2_client.describe_volumes(VolumeIds=[volume_id])
        if response['Volumes']:
            logger.info('      Volume found.')
            volume_exists = True
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)

    return volume_exists


def delete_volume(ec2_client, volume_id, dry_run, logger):
    logger.info(f'   Trying deletion of {volume_id}...')
    deleted = False
    try:
        response = ec2_client.delete_volume(VolumeId=volume_id, DryRun=dry_run)
        logger.info(f'      {response}')
        deleted = True
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        if 'DryRunOperation' in str(e):
            deleted = True

    return deleted


def delete_volumes(ec2_client, client_name, region_name, resource_name, dry_run, run_date_time, logger):
    resource_ids_file_name = f'{client_name} {resource_name}.txt'
    deleted_ids_file_name = f'{client_name} {resource_name} deleted.txt'
    volumes_deleted = 0

    # Copy the resource ids file if a copy doesn't already exist
    file_copy_path = f'{client_name}_{run_date_time}/Copy of {resource_ids_file_name}'
    if not os.path.isfile(file_copy_path):
        shutil.copy(f'{client_name}_{run_date_time}/{resource_ids_file_name}', file_copy_path)
        logger.info('Initial copy of resource ID file was successful.')

    # Read volumes from file
    try:
        with open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'r') as file:
            volumes_list = [line.strip() for line in file]
            logger.info(f'Locating {len(volumes_list)} volumes...')
    except FileNotFoundError:
        logger.info(f'File not found: {resource_ids_file_name}. Skipping volume deletion in {region_name}.')
        return volumes_deleted

    original_volumes_list_length = len(volumes_list)
    volumes_to_delete = []

    # Search for each volume. If it exists, delete the volume
    for volume in volumes_list:
        if get_volume(ec2_client, volume, logger):
            volumes_to_delete.append(volume)
    if volumes_to_delete:
        logger.info(f'\nDeleting {len(volumes_to_delete)} volumes...')
        file = open(f'{client_name}_{run_date_time}/{deleted_ids_file_name}', 'a')
        for vol_to_delete in volumes_to_delete:
            if delete_volume(ec2_client, vol_to_delete, dry_run, logger):
                volumes_deleted += 1
                file.write(vol_to_delete + '\n')
                volumes_list.remove(vol_to_delete)
        file.close()

    logger.info(f'\nNumber of volumes deleted: {volumes_deleted}')
    logger.info(f'Number of remaining volumes: {len(volumes_list)}')

    # Rewrite volumes file if volumes were deleted
    if 0 < len(volumes_list) < original_volumes_list_length:
        logger.info('Rewriting working volumes file...')
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        file = open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'w')
        for volume in volumes_list:
            file.write(volume + '\n')
        file.close()
    elif not volumes_list:
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        logger.info('All volumes deleted. Volumes file removed.')

    return volumes_deleted

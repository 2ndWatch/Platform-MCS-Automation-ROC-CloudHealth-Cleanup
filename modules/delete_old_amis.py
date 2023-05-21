import botocore.exceptions
import sys


def describe_ami_snapshots(client, ami_id, logger):
    response = client.describe_images(ImageIds=[ami_id])
    snapshots = []
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        if 'Ebs' in block_device:
            snapshot_id = block_device['Ebs']['SnapshotId']
            snapshots.append(snapshot_id)
            logger.info(f'  {snapshot_id} from {ami_id}')
    return snapshots


def save_snapshots_to_file(snapshot_ids):
    with open('snapshot_ids.txt', 'a') as file:
        for snapshot_id in snapshot_ids:
            file.write(snapshot_id + '\n')


# have this stop the entire operation if it errors
def deregister_ami(client, ami_id, dry_run, logger):
    logger.info(f'   Trying deregistration of {ami_id}...')
    try:
        response = client.deregister_image(ImageId=ami_id, DryRun=dry_run)
        logger.info(response)
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        # will this work here?
        sys.exit(0)


# have this stop the entire operation if it errors
def delete_snapshot(client, snapshot_id, dry_run, logger):
    logger.info(f'   Trying deletion of {snapshot_id}...')
    try:
        response = client.delete_snapshot(SnapshotId=snapshot_id, DryRun=dry_run)
        logger.info(response)
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        # will this work here?
        sys.exit(0)


def delete_amis(client, dry_run, logger):
    # Read AMI IDs from file
    with open('cypherworx_amis_to_delete.txt', 'r') as file:
        ami_ids = [line.strip() for line in file]

    logger.info('Collection snapshot IDs and deregistering AMIs...')

    for ami_id in ami_ids:
        logger.info(f'\nSearching for {ami_id}...')
        snapshots = describe_ami_snapshots(client, ami_id, logger)
        logger.info(f'      Snapshot list: {snapshots}')
        save_snapshots_to_file(snapshots)
        deregister_ami(client, ami_id, dry_run, logger)

    # Read snapshot IDs from file
    with open('snapshot_ids.txt', 'r') as file:
        snapshot_ids = [line.strip() for line in file]

    for snapshot_id in snapshot_ids:
        logger.info(f'\nSearching for {snapshot_id}...')
        delete_snapshot(client, snapshot_id, dry_run, logger)

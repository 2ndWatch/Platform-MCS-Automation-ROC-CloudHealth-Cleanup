import botocore.exceptions
import os


def describe_ami_snapshots(ec2_client, client_name, image_id, run_date_time, logger):
    error_msg = f'   The image id {image_id} does not exist in this region or account.'
    logger.info(f'   Searching for {image_id}...')
    try:
        response = ec2_client.describe_images(ImageIds=[image_id])
        snapshot_ids = []
        if response['Images']:
            logger.info('      Image found. Getting snapshots...')
            for block_device in response['Images'][0]['BlockDeviceMappings']:
                if 'Ebs' in block_device:
                    snapshot_id = block_device['Ebs']['SnapshotId']
                    snapshot_ids.append(snapshot_id)
            if snapshot_ids:
                with open(f'{client_name}_{run_date_time}/{client_name} old image snaps.txt', 'a') as file:
                    for snapshot_id in snapshot_ids:
                        file.write(snapshot_id + '\n')
            return snapshot_ids
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)


def deregister_ami(ec2_client, image_id, dry_run, logger):
    logger.info(f'   Trying deregistration of {image_id}...')
    try:
        response = ec2_client.deregister_image(ImageId=image_id, DryRun=dry_run)
        logger.info(f'      {response}')
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')


def delete_snapshot(ec2_client, snapshot_id, dry_run, logger):
    logger.info(f'   Trying deletion of {snapshot_id}...')
    try:
        response = ec2_client.delete_snapshot(SnapshotId=snapshot_id, DryRun=dry_run)
        logger.info(f'      {response}')
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')


def delete_old_images(ec2_client, client_name, region_name, dry_run, run_date_time, logger):
    old_images_file_name = f'{client_name} old images.txt'
    image_snaps_file_name = f'{client_name} old image snaps.txt'
    images_deregistered = 0

    # Delete image snapshot file if it exists, to avoid trying to delete snapshots in every region/account
    try:
        os.remove(f'{client_name}_{run_date_time}/{image_snaps_file_name}')
    except FileNotFoundError:
        logger.debug('\nImage snapshot file not found, skipping file deletion.')

    # Read image IDs from file
    try:
        with open(f'{client_name}_{run_date_time}/{old_images_file_name}', 'r') as file:
            image_ids = [line.strip() for line in file]
            logger.info(f'Locating {len(image_ids)} images...')
    except FileNotFoundError:
        logger.info(f'File not found: {old_images_file_name}. Skipping image deregistration in {region_name}.')
        return

    original_image_ids_length = len(image_ids)
    amis_to_deregister = []

    # Search for each image ID. If it exists, add its EBS snapshot IDs to a list, and deregister the image
    for image_id in image_ids:
        ami_snaps = describe_ami_snapshots(ec2_client, client_name, image_id, run_date_time, logger)
        if ami_snaps:
            amis_to_deregister.append(image_id)
            logger.info(f'         {len(ami_snaps)} snapshots for {image_id}: {ami_snaps}')
    if amis_to_deregister:
        logger.info(f'\nDeregistering {len(amis_to_deregister)} images...')
        for image_id in amis_to_deregister:
            deregister_ami(ec2_client, image_id, dry_run, logger)
            images_deregistered += 1
            image_ids.remove(image_id)

    logger.info(f'\nNumber of images deregistered: {images_deregistered}')
    logger.info(f'Number of remaining images: {len(image_ids)}')

    # Rewrite old images file if images were deregistered
    if 0 < len(image_ids) < original_image_ids_length:
        logger.info('Rewriting images file...')
        os.remove(f'{client_name}_{run_date_time}/{old_images_file_name}')
        file = open(f'{client_name}_{run_date_time}/{old_images_file_name}', 'w')
        for image_id in image_ids:
            file.write(image_id + '\n')
        file.close()
    elif not image_ids:
        os.remove(f'{client_name}_{run_date_time}/{old_images_file_name}')
        logger.info('All images deregistered. Old images file replaced.')

    # Read snapshot IDs from file
    try:
        with open(f'{client_name}_{run_date_time}/{image_snaps_file_name}', 'r') as file:
            all_snapshot_ids = [line.strip() for line in file]
    except FileNotFoundError:
        logger.info(f'\nAuto-generated file not found: {image_snaps_file_name}. No snapshots to delete.')
        return

    # If there are snapshot IDs, delete the snapshots
    if all_snapshot_ids:
        logger.info(f'\nDeleting {len(all_snapshot_ids)} associated snapshots...')

        for snapshot_id in all_snapshot_ids:
            delete_snapshot(ec2_client, snapshot_id, dry_run, logger)
    else:
        logger.info('\nEmpty snapshot list. No snapshots to delete.')

    return

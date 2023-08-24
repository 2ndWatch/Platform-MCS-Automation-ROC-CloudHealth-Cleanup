import botocore.exceptions
import os
import shutil


def get_image_snapshots(ec2_client, client_name, image_id, image_snaps_file_name,
                        run_date_time, three_months_date, logger):
    error_msg = f'      The image id {image_id} does not exist in this region or account.'
    logger.info(f'   Searching for {image_id}...')
    try:
        response = ec2_client.describe_images(ImageIds=[image_id])
        snapshot_ids = []
        snaps_to_confirm = []
        confirm_image = False
        if response['Images']:
            image_date = response['Images']['CreationDate'][:10]
            logger.info('      Image found. Getting snapshots...')

            # Check if image is less than three months old
            if image_date > three_months_date:
                logger.info('         Image is less than three months old and needs confirmation.')
                confirm_image = True

            for block_device in response['Images'][0]['BlockDeviceMappings']:
                if 'Ebs' in block_device:
                    snapshot_id = block_device['Ebs']['SnapshotId']
                    snapshot_ids.append(snapshot_id)
            if snapshot_ids:
                with open(f'{client_name}_{run_date_time}/{image_snaps_file_name}', 'a') as file:
                    for snapshot_id in snapshot_ids:
                        file.write(snapshot_id + '\n')
            return snapshot_ids, confirm_image
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)


def deregister_image(ec2_client, image_id, dry_run, logger):
    logger.info(f'   Trying deregistration of {image_id}...')
    deregistered = False
    try:
        response = ec2_client.deregister_image(ImageId=image_id, DryRun=dry_run)
        logger.info(f'      {response}')
        deregistered = True
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        if 'DryRunOperation' in str(e):
            deregistered = True

    return deregistered


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


def delete_images(ec2_client, client_name, region_name, resource_name, dry_run, run_date_time, three_months, logger):
    resource_ids_file_name = f'{client_name} {resource_name}.txt'
    deleted_ids_file_name = f'{client_name} {resource_name} deleted.txt'
    error_ids_file_name = f'{client_name} {resource_name} errors.txt'
    image_snaps_file_name = f'{client_name} {resource_name} snaps.txt'
    images_deregistered = 0
    snapshots_deleted = 0

    # Delete image snapshot file if it exists, to avoid trying to delete snapshots in every region/account
    try:
        os.remove(f'{client_name}_{run_date_time}/{image_snaps_file_name}')
    except FileNotFoundError:
        logger.debug('\nImage snapshot file not found, skipping file deletion.')

    # Read image IDs from file
    try:
        # Copy the resource ids file if a copy doesn't already exist
        file_copy_path = f'{client_name}_{run_date_time}/INPUT {resource_ids_file_name}'
        if not os.path.isfile(file_copy_path):
            shutil.copy(f'{client_name}_{run_date_time}/{resource_ids_file_name}', file_copy_path)
            logger.info('Initial copy of resource ID file was successful.')
        # Read the resource file into a list
        with open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'r') as file:
            image_ids = [line.strip() for line in file]
            logger.info(f'Locating {len(image_ids)} images...')
    except FileNotFoundError:
        logger.info(f'File not found: {resource_ids_file_name}. Skipping image deregistration in {region_name}.')
        return images_deregistered, snapshots_deleted

    original_image_ids_length = len(image_ids)
    images_to_deregister = []
    images_to_confirm = []

    # TODO: new logic
    # for each image id:
    #     send id to api function
    #         return found boolean, confirm boolean & snapshot ids list
    #     if not found:
    #         add to not_processed list
    #     else:
    #         if confirm:
    #             add to confirm list
    #             add snaps to confirm_snaps list
    #         else:
    #             add to delete list
    #             add snaps to delete_snaps list
    #

    # Search for each image ID. If it exists, add its EBS snapshot IDs to a list, and deregister the image
    for image_id in image_ids:
        image_snaps, confirm_image = get_image_snapshots(ec2_client, client_name, image_id, image_snaps_file_name,
                                          run_date_time, three_months, logger)
        if confirm_image:
            images_to_confirm.append(image_id)
        elif image_snaps and not confirm_image:
            images_to_deregister.append(image_id)
            logger.info(f'         {len(image_snaps)} snapshots for {image_id}: {image_snaps}')
    if images_to_deregister:
        logger.info(f'\nDeregistering {len(images_to_deregister)} images...')
        del_file = open(f'{client_name}_{run_date_time}/{deleted_ids_file_name}', 'a')
        err_file = open(f'{client_name}_{run_date_time}/{error_ids_file_name}', 'a')
        errors_list = [line.strip() for line in err_file]
        for image_id in images_to_deregister:
            if image_id not in errors_list:
                if deregister_image(ec2_client, image_id, dry_run, logger):
                    images_deregistered += 1
                    del_file.write(image_id + '\n')
                    image_ids.remove(image_id)
                else:
                    err_file.write(image_id + '\n')
        del_file.close()
        err_file.close()

    logger.info(f'\nNumber of images deregistered: {images_deregistered}')
    logger.info(f'Number of remaining images: {len(image_ids)}')

    # Rewrite old images file if images were deregistered
    if 0 < len(image_ids) < original_image_ids_length:
        logger.info('Rewriting working images file...')
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        file = open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'w')
        for image_id in image_ids:
            file.write(image_id + '\n')
        file.close()
    elif not image_ids:
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        logger.info('All images deregistered. Images file removed.')

    # Read snapshot IDs from file
    try:
        with open(f'{client_name}_{run_date_time}/{image_snaps_file_name}', 'r') as file:
            all_snapshot_ids = [line.strip() for line in file]
        shutil.copy(f'{client_name}_{run_date_time}/{image_snaps_file_name}',
                    f'{client_name}_{run_date_time}/{region_name} {image_snaps_file_name}')
    except FileNotFoundError:
        logger.info(f'\nAuto-generated file not found: {image_snaps_file_name}. No snapshots to delete.')
        return images_deregistered, snapshots_deleted

    # If there are snapshot IDs, delete the snapshots
    if all_snapshot_ids:
        logger.info(f'\nDeleting {len(all_snapshot_ids)} associated snapshots...')

        for snapshot_id in all_snapshot_ids:
            deleted = delete_snapshot(ec2_client, snapshot_id, dry_run, logger)
            if deleted:
                snapshots_deleted += 1
    else:
        logger.info('\nEmpty snapshot list. No snapshots to delete.')

    logger.info(f'\nNumber of snapshots deleted: {snapshots_deleted}')

    return images_deregistered, snapshots_deleted

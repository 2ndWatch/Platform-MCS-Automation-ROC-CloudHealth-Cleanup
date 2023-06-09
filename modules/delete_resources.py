import boto3
import modules.delete_old_images as doi


def delete_resources(profile, client_name, region_name, resource_keys, dry_run, run_date_time, logger):
    account_name = profile['account_name']
    # account_number = profile['account_number']

    session = boto3.Session(region_name=region_name)
    ec2 = session.client('ec2')
    rds = session.client('rds')

    logger.info(f'\n** Starting resource deletion for {account_name} in {region_name}. **')

    ips = 0
    images = 0
    snapshots = 0
    volumes = 0
    rds = 0

    for key in resource_keys:
        if key == '1':
            logger.info('\nUnattached elastic IPS:\n----------------------')
            logger.info('   No action.')
        if key == '2':
            logger.info('\nOld EC2 images:\n--------------')
            images_doi, snapshots_doi = doi.delete_old_images(ec2, client_name, region_name, dry_run,
                                                              run_date_time, logger)
            images += images_doi
            snapshots += snapshots_doi
        if key == '3':
            logger.info('\nOld EBS snapshots:\n-----------------')
            logger.info('   No action.')
        if key == '4':
            logger.info('\nUnused EC2 images:\n-----------------')
            logger.info('   No action.')
        if key == '5':
            logger.info('\nUnattached EBS volumes:\n----------------------')
            logger.info('   No action.')
        if key == '6':
            logger.info('\nOld RDS/Aurora snapshots:\n------------------------')
            logger.info('   No action.')

    return ips, images, snapshots, volumes, rds

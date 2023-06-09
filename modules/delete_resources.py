import boto3
import modules.delete_old_images as doi


def delete_resources(profile, client_name, region_name, resource_keys, dry_run, run_date_time, logger):
    account_name = profile['account_name']
    # account_number = profile['account_number']

    session = boto3.Session(region_name=region_name)
    ec2 = session.client('ec2')
    rds = session.client('rds')

    logger.info(f'\n** Starting resource deletion for {account_name} in {region_name}. **')

    for key in resource_keys:
        if key == '1':
            logger.info('\nUnattached elastic IPS:')
            logger.info('   No action.')
        # TODO: read file here
        if key == '2':
            logger.info('\nOld EC2 images:\n--------------')
            doi.delete_old_images(ec2, client_name, region_name, dry_run, run_date_time, logger)
        if key == '3':
            logger.info('\nOld EBS snapshots:')
            logger.info('   No action.')
        if key == '4':
            logger.info('\nUnused EC2 images:')
            logger.info('   No action.')
        if key == '5':
            logger.info('\nUnattached EBS volumes:')
            logger.info('   No action.')
        if key == '6':
            logger.info('\nOld RDS/Aurora snapshots:')
            logger.info('   No action.')

    return

import boto3


def delete_resources(profile, region_name, resource_keys, logger):
    account_name = profile['account_name']
    # account_number = profile['account_number']

    session = boto3.Session(region_name=region_name)
    ec2 = session.client('ec2')
    rds = session.client('rds')

    logger.info(f'\nStarting resource deletion for {account_name} in {region_name}.')

    for key in resource_keys:
        if key == '1':
            logger.info('\nDeleting unattached elastic IPS...')
        if key == '2':
            logger.info('\nDeleting old EC2 images...')
        if key == '3':
            logger.info('\nDeleting old EBS snapshots...')
        if key == '4':
            logger.info('\nDeleting unused EC2 images...')
        if key == '5':
            logger.info('\nDeleting unattached EBS volumes...')
        if key == '6':
            logger.info('\nDeleting old RDS/Aurora snapshots...')

    return

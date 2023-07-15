import modules.aws_login as aws
import modules.resource_entry_gui as reg
import modules.delete_images as di
import modules.release_ips as ri
import modules.delete_volumes as dv
import modules.delete_ec2_snapshots as des
import modules.delete_rds_snapshots as drs
from botocore.exceptions import ClientError
import aws_sso_lib as sso
import boto3


def create_boto3_session(profile, login, start_url, sso_region, role_name, region):
    if login == 'sso':
        account_id = int(profile['account_number'])
        session = sso.get_boto3_session(start_url, sso_region, account_id, role_name, region=region,
                                        login=False, sso_cache=None, credential_cache=None)
    else:
        session = boto3.Session(region_name=region)
    return session


def delete_resources(profile, client_name, region_name, session, resource_keys, resources_dict, dry_run, run_date_time,
                     logger):
    account_name = profile['account_name']
    account_number = profile['account_number']

    # Create boto3 clients for EC2, RDS
    ec2 = session.client('ec2')
    rds = session.client('rds')

    logger.info(f'\n** Starting resource deletion for {account_name} in {region_name}. **')

    ips = 0
    images = 0
    snapshots = 0
    volumes = 0
    rds_snaps = 0
    unauthorized = []

    for key in resource_keys:
        resource_name = resources_dict[key]

        if key == '1':
            logger.info('\nOld EC2 Image:'
                        '\n-------------')
            try:
                image_count, snapshot_count = di.delete_images(ec2, client_name, region_name, resource_name, dry_run,
                                                               run_date_time, logger)
                images += image_count
                snapshots += snapshot_count
            except ClientError as e:
                if 'UnauthorizedOperation' in str(e):
                    logger.warning(f'   The describe_images or describe_snapshots API call is not authorized in '
                                   f'account {account_number} in the {region_name} region.')
                    unauthorized.append(['old images', account_number, region_name])
                else:
                    logger.warning(e)
        if key == '2':
            logger.info('\nEC2 Image Not Associated:'
                        '\n------------------------')
            try:
                image_count, snapshot_count = di.delete_images(ec2, client_name, region_name, resource_name, dry_run,
                                                               run_date_time, logger)
                images += image_count
                snapshots += snapshot_count
            except ClientError as e:
                if 'UnauthorizedOperation' in str(e):
                    logger.warning(f'   The describe_images or describe_snapshots API call is not authorized in '
                                   f'account {account_number} in the {region_name} region.')
                    unauthorized.append(['unused images', account_number, region_name])
                else:
                    logger.warning(e)
        if key == '3':
            logger.info('\nEC2 Old Snapshots:'
                        '\n-----------------')
            try:
                snapshot_count = des.delete_snapshots(ec2, client_name, region_name, resource_name, dry_run,
                                                      run_date_time, logger)
                snapshots += snapshot_count
            except ClientError as e:
                if 'UnauthorizedOperation' in str(e):
                    logger.warning(
                        f'   The describe_snapshots API call is not authorized in account {account_number} in '
                        f'the {region_name} region.')
                    unauthorized.append(['old EBS snaps', account_number, region_name])
                else:
                    logger.warning(e)
        if key == '4':
            logger.info('\nUnattached Elastic IPs:'
                        '\n----------------------')
            try:
                ip_count = ri.release_ips(ec2, client_name, region_name, resource_name, dry_run,
                                          run_date_time, logger)
                ips += ip_count
            except ClientError as e:
                if 'UnauthorizedOperation' in str(e):
                    logger.warning(
                        f'   The describe_addresses API call is not authorized in account {account_number} in '
                        f'the {region_name} region.')
                    unauthorized.append(['elastic IPs', account_number, region_name])
                else:
                    logger.warning(e)
        if key == '5':
            logger.info('\nUnattached EBS Volumes:'
                        '\n----------------------')
            try:
                volume_count = dv.delete_volumes(ec2, client_name, region_name, resource_name, dry_run,
                                                 run_date_time, logger)
                volumes += volume_count
            except ClientError as e:
                if 'UnauthorizedOperation' in str(e):
                    logger.warning(f'   The describe_volumes API call is not authorized in account {account_number} in '
                                   f'the {region_name} region.')
                    unauthorized.append(['unatt volumes', account_number, region_name])
                else:
                    logger.warning(e)
        if key == '6':
            logger.info('\nRDS Old Snapshots:'
                        '\n-----------------')
            try:
                rds_count = drs.delete_snapshots(rds, client_name, region_name, resource_name, dry_run,
                                                 run_date_time, logger)
                rds_snaps += rds_count
            except ClientError as e:
                if 'AccessDenied' in str(e):
                    logger.warning(
                        f'   The describe_db_snapshots or describe_cluster_snapshots API call is not authorized in '
                        f'account {account_number} in the {region_name} region.')
                    unauthorized.append(['RDS snaps', account_number, region_name])
                else:
                    logger.warning(e)
    return ips, images, snapshots, volumes, rds_snaps, unauthorized


def process_clients(clients_dict, client_keys, resource_keys, resources_dict, dry_run, run_date_time, logger):
    accounts_logged_in = 0
    accounts_not_logged_in_list = []
    clients_logged_in = 0
    clients_not_logged_in_list = []
    unauthorized_list = []

    ips = 0
    images = 0
    snapshots = 0
    volumes = 0
    rds_snaps = 0

    for key in client_keys:
        client_name = clients_dict[key]['name']
        login = clients_dict[key]['login']

        msg = f'Starting resource deletion process for {client_name}.'
        logger.info(f'\n{"+" * len(msg)}'
                    f'\n{msg}'
                    f'\n{"+" * len(msg)}')

        reg.get_resource_ids(client_name, resource_keys, resources_dict, run_date_time, logger)

        for profile in clients_dict[key]['profiles']:
            profile_name = profile['profile_name']
            logged_in = False
            start_url = None
            sso_region = None
            role_name = None

            if login == 'sso':
                start_url = clients_dict[key]['start_url']
                sso_region = clients_dict[key]['sso_region']
                role_name = clients_dict[key]['role_name']

            # log in to the client
            if login == 'sso' or login == 'aal':
                logged_in = aws.aws_login(login, profile, client_name, logger,
                                          start_url=start_url, sso_region=sso_region)
            else:
                logger.info(f'No login type configured for {client_name}. Skipping this client.')
                clients_not_logged_in_list.append(client_name)

            if logged_in:
                if login == 'sso':
                    clients_logged_in += 1
                else:
                    accounts_logged_in += 1

                for region in profile['region']:

                    # create a boto3 session
                    session = create_boto3_session(profile, login, start_url, sso_region, role_name, region)

                    ips_region, images_region, snapshots_region, volumes_region, rds_region, \
                        unauthorized = delete_resources(profile, client_name, region, session, resource_keys,
                                                        resources_dict, dry_run, run_date_time, logger)
                    ips += ips_region
                    images += images_region
                    snapshots += snapshots_region
                    volumes += volumes_region
                    rds_snaps += rds_region

                    for item in unauthorized:
                        unauthorized_list.append(item)
            else:
                if login == 'sso':
                    logger.info(f'You were not logged in, skipping {client_name}.')
                    clients_not_logged_in_list.append(client_name)
                else:
                    logger.info(f'You were not logged in, skipping {profile["profile_name"]}.')
                    accounts_not_logged_in_list.append(profile['profile_name'])
                continue

    logger.debug(f'Did not log into: {accounts_not_logged_in_list}')

    if accounts_logged_in == 0 and clients_logged_in == 0:
        logger.debug('\nNo successful logins recorded. No reports will be generated.')

        # Return if no accounts were accessed
        return 1
    else:
        return accounts_not_logged_in_list, clients_not_logged_in_list, unauthorized_list, ips, images, snapshots, \
            volumes, rds_snaps

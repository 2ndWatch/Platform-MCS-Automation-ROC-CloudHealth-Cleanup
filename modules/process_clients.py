import modules.aws_azure_login as aws
import modules.login_config as lcfg
import modules.resource_entry_gui as reg
import modules.delete_images as di
import modules.release_ips as ri
import modules.delete_volumes as dv
import modules.delete_ec2_snapshots as des
import modules.delete_rds_snapshots as drs
import boto3


def delete_resources(profile, client_name, region_name, resource_keys, resources_dict, dry_run, run_date_time,
                     logger):
    account_name = profile['account_name']

    session = boto3.Session(region_name=region_name)
    ec2 = session.client('ec2')
    rds = session.client('rds')

    logger.info(f'\n** Starting resource deletion for {account_name} in {region_name}. **')

    ips = 0
    images = 0
    snapshots = 0
    volumes = 0
    rds_snaps = 0

    for key in resource_keys:
        resource_name = resources_dict[key]

        if key == '1':
            logger.info('\nEC2 Old Snapshots:'
                        '\n-----------------')
            snapshot_count, error_snap_ids = des.delete_snapshots(ec2, client_name, region_name, resource_name, dry_run,
                                                                  run_date_time, logger)
            snapshots += snapshot_count
        if key == '2':
            logger.info('\nOld EC2 Image:'
                        '\n-------------')
            image_count, snapshot_count = di.delete_images(ec2, client_name, region_name, resource_name, dry_run,
                                                           run_date_time, logger)
            images += image_count
            snapshots += snapshot_count
        if key == '3':
            logger.info('\nEC2 Image Not Associated:'
                        '\n------------------------')
            image_count, snapshot_count = di.delete_images(ec2, client_name, region_name, resource_name, dry_run,
                                                           run_date_time, logger)
            images += image_count
            snapshots += snapshot_count
        if key == '4':
            logger.info('\nUnattached Elastic IPs:'
                        '\n----------------------')
            ip_count = ri.release_ips(ec2, client_name, region_name, resource_name, dry_run,
                                      run_date_time, logger)
            ips += ip_count
        if key == '5':
            logger.info('\nUnattached EBS Volumes:'
                        '\n----------------------')
            volume_count = dv.delete_volumes(ec2, client_name, region_name, resource_name, dry_run,
                                             run_date_time, logger)
            volumes += volume_count
        if key == '6':
            logger.info('\nRDS Old Snapshots:'
                        '\n-----------------')
            rds_count = drs.delete_snapshots(rds, client_name, region_name, resource_name, dry_run,
                                             run_date_time, logger)
            rds_snaps += rds_count
    return ips, images, snapshots, volumes, rds_snaps


def process_clients(clients_dict, client_keys, resource_keys, resources_dict, dry_run, run_date_time, logger):
    accounts_logged_in = 0
    accounts_not_logged_in = 0
    accounts_not_logged_in_list = []

    ips = 0
    images = 0
    snapshots = 0
    volumes = 0
    rds_snaps = 0

    for key in client_keys:
        client_name = clients_dict[key]['name']
        msg = f'Starting resource deletion process for {client_name}.'
        logger.info(f'\n{"+" * len(msg)}'
                    f'\n{msg}'
                    f'\n{"+" * len(msg)}')

        reg.get_resource_ids(client_name, resource_keys, resources_dict, run_date_time, logger)

        for profile in clients_dict[key]['profiles']:
            profile_name = profile['profile_name']

            # Set certain aws-azure-login environmental variables
            lcfg.set_login_credentials(profile, profile_name)

            logger.info(f'\nLogging in to {profile_name}. Enter your Azure credentials in the popup window.')

            # Log into an account (a 'profile') using aws-azure-login
            logged_in = aws.azure_login(profile_name, logger)

            # Delete resources if successfully logged in; otherwise, skip the profile
            if logged_in:
                logger.info(f'You are logged in to {profile["profile_name"]}.')

                for region in profile['region']:
                    ips_region, images_region, snapshots_region, \
                        volumes_region, rds_region = delete_resources(profile, client_name, region, resource_keys,
                                                                      resources_dict, dry_run, run_date_time, logger)
                    ips += ips_region
                    images += images_region
                    snapshots += snapshots_region
                    volumes += volumes_region
                    rds_snaps += rds_region
            else:
                logger.info(f'You were not logged in, skipping {profile["profile_name"]}.')
                accounts_not_logged_in += 1
                accounts_not_logged_in_list.append(profile['profile_name'])
                continue

    logger.debug(f'Did not log into: {accounts_not_logged_in_list}')

    if accounts_not_logged_in > 0 and accounts_logged_in == 0:
        logger.debug('\nNo successful logins recorded. No reports will be generated.')

        # Return if no accounts were accessed
        return 1
    else:
        return accounts_not_logged_in_list, ips, images, snapshots, volumes, rds_snaps

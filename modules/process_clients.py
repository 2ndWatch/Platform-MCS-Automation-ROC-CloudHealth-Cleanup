import modules.aws_azure_login as aws
import modules.login_config as lcfg
import modules.delete_resources as dr
import modules.resource_entry_gui as reg


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
                        volumes_region, rds_region = dr.delete_resources(profile, client_name, region, resource_keys,
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

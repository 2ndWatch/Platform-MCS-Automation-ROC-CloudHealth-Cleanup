import modules.aws_azure_login as aws
import modules.login_config as lcfg
import modules.delete_resources as dr


def process_clients(clients_dict, client_keys, resource_keys, logger):
    for key in client_keys:
        client = clients_dict[key]['name']

        for profile in clients_dict[key]['profiles']:
            profile_name = profile['profile_name']
            lcfg.set_login_credentials(profile, profile_name)

            logger.info(f'\nLogging in to {profile_name}. Enter your Azure credentials in '
                        f'the popup window.')
            logged_in = aws.azure_login(profile_name, logger)

            if logged_in:
                logger.info(f'You are logged in to {profile["profile_name"]}.')

            for region in profile['region']:
                dr.delete_resources(profile, region, resource_keys, logger)

    return

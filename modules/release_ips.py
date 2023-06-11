import botocore.exceptions
import os
import shutil


def get_ip(ec2_client, ip, logger):
    error_msg = f'      The IP {ip} does not exist in this region or account.'
    logger.info(f'   Searching for {ip}...')
    ip_exists = False

    try:
        response = ec2_client.describe_addresses(PublicIps=[ip])
        if response['Addresses']:
            logger.info('      IP found.')
            ip_exists = True
        else:
            logger.info(error_msg)
    except botocore.exceptions.ClientError as e:
        logger.debug(e)
        logger.info(error_msg)

    return ip_exists


def release_ip(ec2_client, ip, dry_run, logger):
    logger.info(f'   Trying release of {ip}...')
    deleted = False
    try:
        response = ec2_client.release_address(PublicIp=ip, DryRun=dry_run)
        logger.info(f'      {response}')
        deleted = True
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
        if 'DryRunOperation' in str(e):
            deleted = True

    return deleted


def release_ips(ec2_client, client_name, region_name, resource_name, dry_run, run_date_time, logger):
    resource_ids_file_name = f'{client_name} {resource_name}.txt'
    ips_released = 0

    # Copy the resource ids file if a copy doesn't already exist
    file_copy_path = f'{client_name}_{run_date_time}/Copy of {resource_ids_file_name}'
    if not os.path.isfile(file_copy_path):
        shutil.copy(f'{client_name}_{run_date_time}/{resource_ids_file_name}', file_copy_path)
        logger.info('Initial copy of resource ID file was successful.')

    # Read IPs from file
    try:
        with open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'r') as file:
            ips_list = [line.strip() for line in file]
            logger.info(f'Locating {len(ips_list)} IPs...')
    except FileNotFoundError:
        logger.info(f'File not found: {resource_ids_file_name}. Skipping IP release in {region_name}.')
        return ips_released

    original_ips_list_length = len(ips_list)
    ips_to_release = []

    # Search for each IP. If it exists, delete the IP
    for ip in ips_list:
        if get_ip(ec2_client, ip, logger):
            ips_to_release.append(ip)
    if ips_to_release:
        logger.info(f'\nReleasing {len(ips_to_release)} IPs...')
        for ip_to_release in ips_to_release:
            if release_ip(ec2_client, ip_to_release, dry_run, logger):
                ips_released += 1
                ips_list.remove(ip_to_release)

    logger.info(f'\nNumber of IPs released: {ips_released}')
    logger.info(f'Number of remaining IPs: {len(ips_list)}')

    # Rewrite IPs file if IPs were deleted
    if 0 < len(ips_list) < original_ips_list_length:
        logger.info('Rewriting working IPs file...')
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        file = open(f'{client_name}_{run_date_time}/{resource_ids_file_name}', 'w')
        for ip in ips_list:
            file.write(ip + '\n')
        file.close()
    elif not ips_list:
        os.remove(f'{client_name}_{run_date_time}/{resource_ids_file_name}')
        logger.info('All IPs released. IPs file removed.')

    return ips_released

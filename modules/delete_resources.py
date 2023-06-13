import boto3
import modules.delete_images as di
import modules.release_ips as ri
import modules.delete_volumes as dv
import modules.delete_ec2_snapshots as des
import modules.delete_rds_snapshots as drs


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
            snapshot_count = des.delete_snapshots(ec2, client_name, region_name, resource_name, dry_run,
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

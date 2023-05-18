import boto3
import botocore.exceptions
import time
from datetime import datetime
import sys
import logging

logger = logging.getLogger('2wchclean')
logging.basicConfig(level=logging.DEBUG,
                    filename=f'log/2wchclean_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.log',
                    filemode='a')
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logger.addHandler(console)

DRY_RUN = False


def describe_ami_snapshots(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    response = ec2_client.describe_images(ImageIds=[ami_id])
    snapshots = []
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        if 'Ebs' in block_device:
            snapshot_id = block_device['Ebs']['SnapshotId']
            snapshots.append(snapshot_id)
            logger.info(f'  {snapshot_id} from {ami_id}')
    # time.sleep(0.1)
    return snapshots


def save_snapshots_to_file(snapshot_ids):
    with open('snapshot_ids.txt', 'a') as file:
        for snapshot_id in snapshot_ids:
            file.write(snapshot_id + '\n')


# have this stop the entire operation if it errors
def deregister_ami(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    logger.info(f'   Trying deregistration of {ami_id}...')
    try:
        response = ec2_client.deregister_image(ImageId=ami_id, DryRun=DRY_RUN)
        logger.info(response)
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
    # time.sleep(0.1)


# have this stop the entire operation if it errors
def delete_snapshot(snapshot_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    logger.info(f'   Trying deletion of {snapshot_id}...')
    try:
        response = ec2_client.delete_snapshot(SnapshotId=snapshot_id, DryRun=DRY_RUN)
        logger.info(response)
    except botocore.exceptions.ClientError as e:
        logger.info(f'      {e}')
    # time.sleep(0.1)


def main():
    # Read AMI IDs from file
    with open('cypherworx_amis_to_delete.txt', 'r') as file:
        ami_ids = [line.strip() for line in file]

    # Specify the AWS CLI profile
    aws_profile = 'cypherworxmain'

    logger.info('Collection snapshot IDs and deregistering AMIs...')

    for ami_id in ami_ids:
        logger.info(f'\nSearching for {ami_id}...')
        snapshots = describe_ami_snapshots(ami_id, aws_profile)
        logger.info(f'      Snapshot list: {snapshots}')
        save_snapshots_to_file(snapshots)
        deregister_ami(ami_id, aws_profile)

    # Read snapshot IDs from file
    with open('snapshot_ids.txt', 'r') as file:
        snapshot_ids = [line.strip() for line in file]

    for snapshot_id in snapshot_ids:
        logger.info(f'\nSearching for {snapshot_id}...')
        delete_snapshot(snapshot_id, aws_profile)


main()
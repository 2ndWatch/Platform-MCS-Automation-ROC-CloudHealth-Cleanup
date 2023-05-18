import boto3
import botocore.exceptions
import time

DRY_RUN = True


def describe_ami_snapshots(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    response = ec2_client.describe_images(ImageIds=[ami_id])
    snapshots = []
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        if 'Ebs' in block_device:
            snapshot_id = block_device['Ebs']['SnapshotId']
            snapshots.append(snapshot_id)
            print(f'  {snapshot_id} from {ami_id}')
    time.sleep(0.1)
    return snapshots


def save_snapshots_to_file(snapshot_ids):
    with open('snapshot_ids.txt', 'a') as file:
        for snapshot_id in snapshot_ids:
            file.write(snapshot_id + '\n')


def deregister_ami(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    print(f'   Trying deregistration of {ami_id}...')
    try:
        response = ec2_client.deregister_image(ImageId=ami_id, DryRun=DRY_RUN)
        print(response)
    except botocore.exceptions.ClientError as e:
        print(f'      {e}')
    time.sleep(0.1)


def delete_snapshot(snapshot_id, profile_name):
    session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
    ec2_client = session.client('ec2')
    print(f'   Trying deletion of {snapshot_id}...')
    try:
        response = ec2_client.delete_snapshot(SnapshotId=snapshot_id, DryRun=DRY_RUN)
        print(response)
    except botocore.exceptions.ClientError as e:
        print(f'      {e}')
    time.sleep(0.1)


def main():
    # Read AMI IDs from file
    with open('amis_test.txt', 'r') as file:
        ami_ids = [line.strip() for line in file]

    # Specify the AWS CLI profile
    aws_profile = 'cypherworxmain'

    print('Collection snapshot IDs and deregistering AMIs...')

    for ami_id in ami_ids:
        print(f'\nSearching for {ami_id}...')
        snapshots = describe_ami_snapshots(ami_id, aws_profile)
        print(f'      Snapshot list: {snapshots}')
        save_snapshots_to_file(snapshots)
        deregister_ami(ami_id, aws_profile)

    # Read snapshot IDs from file
    with open('snapshot_ids.txt', 'r') as file:
        snapshot_ids = [line.strip() for line in file]

    for snapshot_id in snapshot_ids:
        print(f'\nSearching for {snapshot_id}...')
        delete_snapshot(snapshot_id, aws_profile)


main()

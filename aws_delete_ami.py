import boto3

DRY_RUN = True


def describe_ami_snapshots(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name)
    ec2_client = session.client('ec2')
    response = ec2_client.describe_images(ImageIds=[ami_id])
    snapshots = []
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        if 'Ebs' in block_device:
            snapshot_id = block_device['Ebs']['SnapshotId']
            snapshots.append(snapshot_id)
    return snapshots


def save_snapshots_to_file(snapshot_ids):
    with open('snapshot_ids.txt', 'a') as file:
        for snapshot_id in snapshot_ids:
            file.write(snapshot_id + '\n')


def deregister_ami(ami_id, profile_name):
    session = boto3.Session(profile_name=profile_name)
    ec2_client = session.client('ec2')
    ec2_client.deregister_image(ImageId=ami_id, DryRun=DRY_RUN)


def delete_snapshot(snapshot_id, profile_name):
    session = boto3.Session(profile_name=profile_name)
    ec2_client = session.client('ec2')
    ec2_client.delete_snapshot(ImageId=snapshot_id, DryRun=DRY_RUN)


def main():
    # Read AMI IDs from file
    with open('cypherworx_amis_to_delete.txt', 'r') as file:
        ami_ids = [line.strip() for line in file]

    # Specify the AWS CLI profile
    aws_profile = 'your_aws_profile'

    for ami_id in ami_ids:
        snapshots = describe_ami_snapshots(ami_id, aws_profile)
        save_snapshots_to_file(snapshots)
        deregister_ami(ami_id, aws_profile)

    # Read snapshot IDs from file
    with open('snapshot_ids.txt', 'r') as file:
        snapshot_ids = [line.strip() for line in file]

    for snapshot_id in snapshot_ids:
        delete_snapshot(snapshot_id, aws_profile)


main()

import modules.process_clients as pc
from src.banner import banner
from datetime import datetime
import os
import sys
import logging
import json
import easygui as eg

run_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")

logger = logging.getLogger('2wchclean')
logging.basicConfig(level=logging.DEBUG,
                    filename=f'log/2wchclean_{run_date_time}.log',
                    filemode='a')
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logger.addHandler(console)

with open('src/clients.txt') as cl:
    cl_txt = cl.read()
clients_dict = json.loads(cl_txt)


def parse_selection(choices):
    # Create list of keys and names from client or resource selection
    keys = [choice.split(' ')[0] for choice in choices]
    names = []
    for choice in choices:
        choice_split = choice.split(' ')
        name = choice_split[1]
        if len(choice_split) > 2:
            for i in range(2, len(choice_split)):
                name += f' {choice_split[i]}'
        names.append(name)
    return keys, names


def create_directories(choices):
    for choice in choices:
        new_dir = f'{choice}_{run_date_time}'
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
    return


def main(clients):
    print(banner)
    logger.info('\nWelcome to the 2nd Watch Cloud Health resource deletion program.\n')
    # Welcome message box
    welcome = eg.msgbox('Welcome to the 2nd Watch Cloud Health resource deletion program.'
                        '\n\nClick the <Begin> button to proceed.',
                        '2nd Watch Cloud Health Resource Deleter', ok_button='Begin')
    if welcome is None:  # User closed msgbox
        sys.exit(0)

    # Create a list of clients from which to select
    client_choices = []
    for key, value in clients.items():
        client_choices.append(f'{key} {value["name"]}')

    resources_dict = {
        '1': 'EC2 Old Snapshots',
        '2': 'Old EC2 Image',
        '3': 'EC2 Image Not Associated',
        '4': 'Unattached Elastic IPs',
        '5': 'Unattached EBS Volumes',
        '6': 'RDS Old Snapshots'
    }

    resource_choices = []
    for key, value in resources_dict.items():
        resource_choices.append(f'{key} {value}')
    logger.info(resource_choices)

    while 1:
        selected_clients = eg.multchoicebox('Select one or multiple clients by left-clicking.'
                                            '\n\nlick the <Cancel> button to exit.',
                                            'Client Selection', client_choices, preselect=None)
        if selected_clients is None:
            sys.exit(0)

        client_keys, client_names = parse_selection(selected_clients)
        logger.info(f'Client keys: {client_keys}')
        logger.info(f'You are running the program for: {client_names}')

        # Create directories for selected clients
        logger.info('\nCreating directories for client(s)...')
        create_directories(client_names)

        selected_resources = eg.multchoicebox('Select one or multiple resources by left-clicking.'
                                              '\n\nClick the <Cancel> button to exit.',
                                              'Resource Selection', resource_choices, preselect=None)
        if selected_resources is None:
            sys.exit(0)

        resource_keys, resource_names = parse_selection(selected_resources)
        logger.info(f'Resource keys: {resource_keys}')
        logger.info(f'You are running the program for: {resource_names}')

        # Returns True for Dry Run and False for Delete Stuff
        dry_run = eg.ccbox('! ! !   IMPORTANT   ! ! !'
                           '\n\nIf you are TESTING, click the <Dry Run> button.'
                           '\n\nIf you intend to actually delete resources, click the <Delete Stuff> button.'
                           '\n\nYour selection will show in the next window. If you click the wrong button by mistake, '
                           'you will be able to exit the program and try again.',
                           title='Dry Run/Delete Stuff', choices=['Dry Run', 'Delete Stuff'], cancel_choice='Dry Run')
        if not dry_run:
            sys.exit(0)

        logger.info(f'\nDry run is set to {dry_run}.')

        ready = eg.ccbox(f'You chose: {resource_names}\n   for {client_names}.'
                         f'\n\nThis is a DRY RUN: {dry_run}.'
                         f'\nMake sure this is what you intend. If not, exit the program and start over.'
                         f'\n\nYou can track deletion progress in the console window.'
                         f'\n\nClick the <Run> button to begin resource deletion.'
                         f'\nClick the <Exit> button to exit the program without deleting any resources.',
                         title='Selection Result', choices=['Run', 'Exit'], cancel_choice='Exit')
        if not ready:
            sys.exit(0)

        process_result, ips, images, snapshots, volumes, rds = pc.process_clients(clients_dict, client_keys,
                                                                                  resource_keys, resources_dict,
                                                                                  dry_run, run_date_time, logger)

        if process_result == 1:

            # No logins were successful
            logger.info('\nNo successful logins recorded. No resources were deleted.')

            eg.msgbox(f'No successful logins recorded. No resources were deleted.'
                      f'\n\nPlease submit the log file from this run attempt.'
                      f'\n\nClick the <Exit> button to exit the program.',
                      'Resource Deletion Result', ok_button='Exit')
        else:

            # At least one login was successful; displays any logins that did not succeed
            logger.info(f'\nResource deletion is complete. If this was a dry run --> [{dry_run}] <-- then no resources '
                        f'were actually deleted.'
                        f'\n\nSummary:'
                        f'\nIPs deleted: {ips}'
                        f'\nImages deregistered: {images}'
                        f'\nEBS snapshots deleted: {snapshots}'
                        f'\nVolumes deleted: {volumes}'
                        f'\nRDS snapshots deleted: {rds}'
                        f'\n\nAccounts not logged into: {process_result}'
                        f'\n\nClient directories for this run are appended with {run_date_time}.'
                        f'\n\nThe log file can be found in the <log> directory.')

            eg.msgbox(f'Resource deletion is complete. If this was a dry run --> [{dry_run}] <-- then no resources '
                      f'were actually deleted.'
                      f'\n\nSummary:'
                      f'\nIPs deleted: {ips}'
                      f'\nImages deregistered: {images}'
                      f'\nEBS snapshots deleted: {snapshots}'
                      f'\nVolumes deleted: {volumes}'
                      f'\nRDS snapshots deleted: {rds}'
                      f'\n\nAccounts not logged into: {process_result}'
                      f'\n\nClient directories for this run are appended with {run_date_time}.'
                      f'\n\nThe log file can be found in the <log> directory.'
                      f'\n\nClick the <Exit> button to exit the program.',
                      'Resource Deletion Result', ok_button='Exit')

        return


main(clients_dict)

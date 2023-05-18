from src.banner import banner
from datetime import datetime
import sys
import logging
import json
import easygui as eg

logger = logging.getLogger('2wchclean')
logging.basicConfig(level=logging.DEBUG,
                    filename=f'log/2wchclean_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.log',
                    filemode='a')
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logger.addHandler(console)

with open('src/clients.txt') as cl:
    cl_txt = cl.read()
clients_dict = json.loads(cl_txt)

# Set to True for unit tests
TESTING = False

# Set to True to validate access prior to deleting resources
DRY_RUN = False


def parse_selection(choices):
    # Create list of keys and names from clint or resource selection
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


def main(clients):
    print(banner)
    logger.info('\nWelcome to the 2nd Watch Cloud Health resource deletion program.\n')
    # Welcome message box
    welcome = eg.msgbox('Welcome to the 2nd Watch Cloud Health resource deletion program.\n\n'
                        'Click the <OK> button to proceed.',
                        '2nd Watch Cloud Health Resource Deleter')
    if welcome is None:  # User closed msgbox
        sys.exit(0)

    # Create a list of clients from which to select
    client_choices = []
    for key, value in clients.items():
        client_choices.append(f'{key} {value["name"]}')

    resource_choices = [
        '1 Unallocated Elastic IPs',
        '2 Old EC2 Images',
        '3 Old EBS Snapshots',
        '4 Old Unused EC2 Images',
        '5 Old Unattached EBS Volumes',
        '6 Old RDS/Aurora Snapshots'
    ]

    while 1:
        selected_clients = eg.multchoicebox('Select one or multiple clients by left-clicking.\n\n'
                                            'Click the <Cancel> button to exit.',
                                            'Client Selection', client_choices, preselect=None)
        if selected_clients is None:
            sys.exit(0)

        client_keys, client_names = parse_selection(selected_clients)
        logger.info(f'Client keys: {client_keys}')
        logger.info(f'You are running the program for: {client_names}')

        selected_resources = eg.multchoicebox('Select one or multiple resources by left-clicking.\n\n'
                                              'Click the <Cancel> button to exit.',
                                              'Resource Selection', resource_choices, preselect=None)
        if selected_resources is None:
            sys.exit(0)

        resource_keys, resource_names = parse_selection(selected_resources)
        logger.info(f'Resource keys: {client_keys}')
        logger.info(f'You are running the program for: {resource_names}')

        eg.msgbox(f'You chose to delete: {resource_names}\n   for {client_names}.\n\n'
                  f'Click the <OK> button to begin resource deletion.\n\n'
                  f'You can track deletion progress in the console window.',
                  'Selection Result')

        # Actually do all the things here
        print('\nPretending to do all the things now.')

        logger.info('\nResource deletion is complete. Log files can be found in the <log> directory.')

        eg.msgbox(f'Resource deletion is complete. Log files can be found in the <log> directory.\n\n'
                  f'Please run the program again if you want to delete more resources.\n\n'
                  f'Click the <OK> button to exit the program.',
                  'Resource Deletion Result')

        return


main(clients_dict)

import easygui as eg
import sys


def get_resource_ids_list(client_name, resource_keys, resources_dict, run_date_time, logger):
    resource_ids_list = [[], [], [], [], [], []]

    for key in resource_keys:
        resource_name = resources_dict[key]
        entry = eg.enterbox(f'Enter resource IDs for:'
                            f'\n\nClient: {client_name}'
                            f'\nResource: {resource_name}'
                            f'\n\nCopy/paste directly from Excel. Disregard the strange-looking formatting in the '
                            f'entry field.'
                            f'\n\nIf there are no resources to enter, leave the entry field blank and click the '
                            f'<OK> button.',
                            title=f'{client_name} {resource_name} Resource Entry')
        if entry is None:
            sys.exit(0)

        if entry:
            entry_list = entry.split('\n')
            logger.info(f'\n{resource_name}: {entry_list}')
            resource_ids_list[int(key) - 1] = entry_list

            # Write a file of each resource ID set for backup reference
            file = open(f'{client_name}_{run_date_time}/{client_name} {resource_name}.txt', 'w')
            for i in range(len(entry_list)):
                if i == (len(entry_list) - 1):
                    file.write(entry_list[i])
                else:
                    file.write(entry_list[i] + '\n')
            file.close()

    return

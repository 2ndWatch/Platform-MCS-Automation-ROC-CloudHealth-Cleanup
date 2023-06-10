import easygui as eg
import sys
import os


def get_resource_ids(client_name, resource_keys, resources_dict, run_date_time, logger):
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

            confirmed = eg.ynbox(f'You have entered {len(entry_list)} {resource_name} IDs:'
                                 f'\n\n{os.linesep.join(f"{entry}" for entry in entry_list)}'
                                 f'\n\nIs this correct?', title='Confirm Resource ID Entry')

            # This could either skip the resource, or quit the program; currently skips the resource.
            if not confirmed:
                logger.info(f'{resource_name} resources not confirmed. No file written.')
                # sys.exit(0)
            else:
                logger.info(f'\n{resource_name}: {entry_list}')
                resource_ids_list[int(key) - 1] = entry_list

                # Write a file of each resource ID set for backup reference
                try:
                    file = open(f'{client_name}_{run_date_time}/{client_name} {resource_name}.txt', 'w')
                    for i in range(len(entry_list)):
                        if i == (len(entry_list) - 1):
                            file.write(entry_list[i])
                        else:
                            file.write(entry_list[i] + '\n')
                    file.close()
                    logger.info(f'"{client_name} {resource_name}.txt" written successfully.')
                except FileNotFoundError:
                    logger.info(f'Something went wrong when trying to write "{client_name} {resource_name}.txt".')
        else:
            logger.info(f'{resource_name} resources not entered. No file written.')

    return

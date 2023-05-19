import subprocess


def azure_login(profile_name, logger):

    is_logged_in = False

    login = subprocess.Popen(['aws-azure-login', '--profile', f'{profile_name}', '--mode', 'gui'], shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = login.communicate()
    logger.debug(output)
    logger.debug(errors)
    login.wait()

    # Verify login status
    login_verify = subprocess.Popen(['aws', 'sts', 'get-caller-identity'], shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = login_verify.communicate()
    login_verify.wait()
    # print(output)

    if 'UserId' in output:
        is_logged_in = True

    return is_logged_in

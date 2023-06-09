import subprocess


def azure_login(profile_name, logger):

    is_logged_in = False

    # Run 'aws-azure-login --profile foo --mode gui' in a subprocess shell
    login = subprocess.Popen(['aws-azure-login', '--profile', f'{profile_name}', '--mode', 'gui'],
                             shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = login.communicate()
    logger.debug(output)
    logger.debug(errors)
    login.wait()

    # Verify login status with an STS API call
    login_verify = subprocess.Popen(['aws', 'sts', 'get-caller-identity'], shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = login_verify.communicate()
    logger.debug(output)
    logger.debug(errors)
    login_verify.wait()

    if 'UserId' in output:
        is_logged_in = True

    return is_logged_in

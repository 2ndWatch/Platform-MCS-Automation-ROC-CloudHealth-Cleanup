import os


def set_login_credentials(profile):

    os.environ['AZURE_TENANT_ID'] = profile['tenant_id']
    os.environ['AZURE_APP_ID_URI'] = profile['app_id_uri']
    os.environ['AZURE_DEFAULT_ROLE_ARN'] = ''
    os.environ['AZURE_DEFAULT_DURATION_HOURS'] = '1'

    return
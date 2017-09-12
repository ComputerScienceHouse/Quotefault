import os

# Flask config
DEBUG = False
IP = os.environ.get('QUOTEFAULT_IP', '127.0.0.1')
PORT = os.environ.get('QUOTEFAULT_PORT', '8080')
SERVER_NAME = os.environ.get('QUOTEFAULT_SERVER_NAME', 'quotefault.csh.rit.edu')
PLUG = True
#db info
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///{}'.format(os.path.join(os.getcwd(), "data.db")))
#DB_HOST = os.environ.get('QUOTEFAULT_DB_HOST', 'mysql.csh.rit.edu')
#DB_USERNAME = os.environ.get('QUOTEFAULT_DB_USERNAME', 'quotefault')
#DB_NAME = os.environ.get('QUOTEFAULT_DB_NAME', 'quotefault')
#DB_PASSWORD = os.environ.get('QUOTEFAULT_DB_PASSWORD', '')
# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get('QUOTEFAULT_OIDC_ISSUER', 'https://sso.csh.rit.edu/realms/csh')
OIDC_CLIENT_CONFIG = {
    'client_id': os.environ.get('QUOTEFAULT_OIDC_CLIENT_ID', 'quotefault'),
    'client_secret': os.environ.get('QUOTEFAULT_OIDC_CLIENT_SECRET', ''),
    'post_logout_redirect_uris': [os.environ.get('QUOTEFAULT_OIDC_LOGOUT_REDIRECT_URI', 'https://quotefault.csh.rit.edu/logout')]
}

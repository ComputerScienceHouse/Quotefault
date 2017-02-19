# Flask config
DEBUG = False
IP = '127.0.0.1'
PORT = '8080'
SERVER_NAME = 'localhost:8080'
#db info
DB_HOST = 'mysql.csh.rit.edu'
DB_USERNAME = 'quotefault'
DB_NAME = 'quotefault'
DB_PASSWORD = ''
# OpenID Connect SSO config
OIDC_ISSUER = 'https://sso.csh.rit.edu/realms/csh'
OIDC_CLIENT_CONFIG = {
    'client_id': 'quotefault',
    'client_secret': 'lolno',
    'post_logout_redirect_uris': ['http://localhost:8080/logout']
}
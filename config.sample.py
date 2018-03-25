import os

# Flask config
DEBUG = False
IP = '127.0.0.1'
PORT = '8080'
SERVER_NAME = 'localhost:8080'
PLUG = True
#db info
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(os.getcwd(), "data.db"))

# OpenID Connect SSO config
OIDC_ISSUER = 'https://sso.csh.rit.edu/auth/realms/csh'
OIDC_CLIENT_CONFIG = {
    'client_id': 'quotefault',
    'client_secret': 'lolno',
    'post_logout_redirect_uris': ['http://localhost:8080/logout']
}

# CSH_LDAP credentials
LDAP_BIND_DN = ''
LDAP_BIND_PW = ''

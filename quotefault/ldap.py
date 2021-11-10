"""
File name: mail.py
Author: Nicholas Mercadante
"""
from functools import lru_cache
from csh_ldap import CSHLDAP
from quotefault import app

# Create CSHLDAP connection
_ldap = CSHLDAP(app.config["LDAP_BIND_DN"],
                app.config["LDAP_BIND_PW"])

@lru_cache(maxsize=8192)
def get_all_members():
    """
    Get all CSH Members
    """
    return [{"uid": member.get("uid")[0], "cn": member.get("cn")[0]} for member in
            _ldap.get_group('member').get_members()]


@lru_cache(maxsize=8192)
def ldap_get_member(username):
    """
    Receive specific member's information based on UID
    """
    return _ldap.get_member(username, uid=True)


@app.context_processor
def utility_processor():
    """
    Get a members actual name based on uid
    """
    def get_display_name(username):
        try:
            member = ldap_get_member(username)
            return member.cn + " (" + member.uid + ")"
        except:
            return username
    return dict(get_display_name=get_display_name)

def is_member_of_group(uid: str, group: str) -> bool:
    """
    Determine if user is member of LDAP group
    """
    member = ldap_get_member(uid)
    group_list = member.get("memberOf")
    for group_dn in group_list:
        if group == group_dn.split(",")[0][3:]:
            return True
    return False

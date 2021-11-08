from functools import lru_cache
from quotefault import _ldap, app
from typing import Dict, List
import ldap as pyldap  # type: ignore
from typing import Optional, List, Dict
from csh_ldap import CSHLDAP, CSHMember


@lru_cache(maxsize=8192)
def get_all_members():
    return [{"uid": member.get("uid")[0], "cn": member.get("cn")[0]} for member in
            _ldap.get_group('member').get_members()]


@lru_cache(maxsize=8192)
def ldap_get_member(username):
    return _ldap.get_member(username, uid=True)


@app.context_processor
def utility_processor():
    def get_display_name(username):
        try:
            member = ldap_get_member(username)
            return member.cn + " (" + member.uid + ")"
        except:
            return username
    return dict(get_display_name=get_display_name)

def is_member_of_group(uid: str, group: str) -> bool:
    member = ldap_get_member(uid)
    group_list = member.get("memberOf")
    for group_dn in group_list:
        if group == group_dn.split(",")[0][3:]:
            return True
    return False
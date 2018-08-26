from functools import lru_cache
from quotefault import _ldap, app


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

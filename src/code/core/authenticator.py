#!/usr/bin/env python

import sys
from core.config import settings as cfg


class Authenticator:
    def __init__(self, **kwargs):
        pass

    @property
    def use_token(self):
        return False

    def validate(self, username, password):
        return False

    @property
    def roles(self):
        return []


class LocalAuth(Authenticator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def use_token(self):
        return True

    def validate(self, username, password):
        return True
    
    @property
    def roles(self):
        return ["global"]


class ConfigAuth(Authenticator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def use_token(self):
        return False

    def validate(self, username, password):
        return True
    
    @property
    def roles(self):
        return ["global"]


class LDAPAuth(Authenticator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def use_token(self):
        return False


def get_authenticator():
    if cfg.sys_authenticator.get("type", "local") == "local":
        return LocalAuth()
    elif cfg.sys_authenticator.get("type", "local") == "config":
        return ConfigAuth()
    elif cfg.sys_authenticator.get("type", "local") in "ldap":
        return LDAPAuth(microsoft=True)
    elif cfg.sys_authenticator.get("type", "local") == "openldap":
        return LDAPAuth()
    
    return Authenticator()

authenticator = get_authenticator()

if __name__ == "__main__":
    print("Location: /\n")
    sys.exit()
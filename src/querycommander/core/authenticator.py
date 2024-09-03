import sys
import logging
import ldap3
from querycommander.core.config import settings as cfg
from querycommander.core.helpers import validate_string


class Authenticator:
    def __init__(self, **kwargs):
        self.logger = logging.getLogger("AUTHENTICATOR")
        self.logger.setLevel(cfg.log_level)

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

class LDAPAuth(Authenticator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = kwargs

        self.microsoft = kwargs.get("microsoft", False)
        self.use_friendly_names = kwargs.get("options", {}).get("use_friendly_names", True) # When False, requires full group DN to be specified as role in settings file
        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port")
        self.use_ssl = kwargs.get("options", {}).get("ssl", False)
        self.login_is_role = kwargs.get("options", {}).get("login_is_role", False)
        self.conn_options = kwargs.get("extra_args", {})

        self.ldap_base_dn = kwargs.get("options", {}).get("base_dn")  # example only: "dc=example,dc=com"
        if self.ldap_base_dn is None:
            raise ValueError("No LDAP Base DN was specified.")
            
        if self.microsoft:
            # Active Directory (uses memberOf attribute on user for group DNs)
            self.user_search_filter = kwargs.get("options", {}).get("user_search_filter", "(&(objectClass=user)(sAMAccountName={USERNAME}))")
            self.user_domain_separator = kwargs.get("options", {}).get("domain_separator", "\\")
            self.user_pattern = kwargs.get("options", {}).get("user_pattern")
            self.user_group_search_filter = None
            #self.user_group_search_filter = kwargs.get("options", {}).get("user_group_search_filter", "")

        else:
            # OpenLDAP (has to search for groups to see who is a member)
            self.user_search_filter = kwargs.get("options", {}).get("user_search_filter", "(&(objectClass=person)(uid={USERNAME}))")
            self.user_pattern = kwargs.get("options", {}).get("user_pattern")  # example only:  "uid={USERNAME},ou=people,dc=example,dc=com"
            self.user_group_search_filter = kwargs.get("options", {}).get("user_group_search_filter", "(&(objectClass=posixGroup)(memberUid={USERNAME}))")

            if self.user_pattern is None:
                raise ValueError("No LDAP User Pattern was specified.")

        if self.port is not None:
            self.port = int(self.port)

        self.server = ldap3.Server(self.host, port=self.port, use_ssl=self.use_ssl)
        self.conn = None

        self.username = None
        self.domain = None
        self.ldap_user = None
    
    def _get_groups_microsoft(self):
        if self.conn is None:
            return []

        groups = []

        try:
            self.conn.search(
                search_base=self.ldap_base_dn,
                search_filter=self.user_search_filter.format(USERNAME=self.username),
                attributes=['sAMAccountName','memberOf']
            )

            if isinstance(self.conn.entries, list) and len(self.conn.entries) > 0:
                #logging.debug(str([entry.cn.value for entry in self.conn.entries]))
                for entry in self.conn.entries:
                    if str(entry.sAMAccountName.value).lower() == str(self.username).lower():
                        user_group_list = entry.memberOf.value
                        for group_dn in user_group_list:
                            groups.append(group_dn.split(",", 1)[0].split("=", 1)[1].replace("\\#","#"))

                        break

        except:
            self.logger.error(f"[LDAP {self.host}] Group search failed")
            self.logger.debug(f"[LDAP {self.host}] {str(sys.exc_info()[0])}")
            pass

        return groups

    def _get_groups_openldap(self):
        if self.conn is None:
            return []
        
        try:
            self.conn.search(
                search_base=self.ldap_base_dn,
                search_filter=self.user_group_search_filter.format(USERNAME=self.username),
                search_scope=ldap3.SUBTREE,
                attributes=["cn"]
            )

            if isinstance(self.conn.entries, list) and len(self.conn.entries) > 0:
                #logging.debug(str([entry.cn.value for entry in self.conn.entries]))
                return [entry.cn.value for entry in self.conn.entries]

        except Exception:
            self.logger.error(f"[LDAP {self.host}] Group search failed")
            self.logger.debug(f"[LDAP {self.host}] {str(sys.exc_info()[0])}")
            pass
        
        return []

    def unbind(self):
        try:
            if self.conn is not None:
                self.conn.unbind()
        except:
            self.logger.error(f"[LDAP {self.host}] Unbind error, skipping")
            self.logger.debug(f"[LDAP {self.host}] {str(sys.exc_info()[0])}")
            return False
        
        return True

    def validate(self, username, password):
        ldap_login = None
        if self.microsoft:
            if "\\" in username:
                self.username = username.split("\\",1)[1]
                self.domain = username.split("\\",1)[0]

                if not validate_string(self.domain, is_username=True, max_length=15):
                    return False

                if not validate_string(self.username, is_username=True, max_length=20):
                    return False

            else:
                return False

            ldap_login = f"{self.domain}{self.user_domain_separator}{self.username}"
            self.ldap_user = self.username

            if self.user_pattern is not None:
                self.ldap_user = self.user_pattern.format(USERNAME=self.username)

                ldap_login = self.ldap_user

        else:
            if not validate_string(username, is_username=True, max_length=255):
                return False
            
            self.username = username
            self.ldap_user = self.user_pattern.format(USERNAME=username)
            ldap_login = self.ldap_user

        try:
            if self.conn is None:
                self.conn = ldap3.Connection(self.server, user=ldap_login, password=password, auto_bind=True, **self.conn_options)

            # If we reach this line then the login was valid

        except Exception:
            self.logger.error(f"[LDAP {self.host}] LDAP credential validation failed for user: {username}")
            self.logger.debug(f"[LDAP {self.host}] {str(sys.exc_info()[0])}")
            return False

        return True
    
    @property
    def roles(self):
        if self.login_is_role:
            return [self.username]
        else:
            if self.microsoft:
                return self._get_groups_microsoft()
            else:
                return self._get_groups_openldap()


def get_authenticator(connection_details):
    if connection_details.get("type", "local") == "local":
        return LocalAuth(**connection_details)
    elif connection_details.get("type", "local") in ["ldap", "microsoft"]:
        return LDAPAuth(microsoft=True, **connection_details)
    elif connection_details.get("type", "local") == "openldap":
        return LDAPAuth(**connection_details)
    
    return Authenticator(**connection_details)

#authenticator = get_authenticator(cfg.sys_authenticator)

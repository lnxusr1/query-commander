# Authentication

## Local Database Authentication

The most basic method of authentication is to leverage standard local database authentication.  This method asks for the end-users login and password and then uses those credentials directly to log into the database connections configured.

To enable local authentication enter the following in the *settings.yml* file:

``` yaml
authenticator:
  type: local
```

## LDAP Authentication (OpenLDAP)

Simple example of authenticating using OpenLDAP is shown below:

``` yaml
authenticator:
  type: openldap
  host: my-ldap-server
  port: 389
  options:
    login_is_role: false
    base_dn: dc=example,dc=com
    user_search_filter: (&(objectClass=person)(uid={USERNAME}))
    user_pattern: uid={USERNAME},ou=people,dc=example,dc=com
    user_group_search_filter: (&(objectClass=posixGroup)(memberUid={USERNAME}))
```

The **user_pattern** option is used to specify a "wrapper" for plain usernames when attempting to authenticate to the server.  The example above would take the username *lnxusr1* entered in the username box in the app and translate it to *uid=lnxusr1,ou=people,dc=example,dc=com* when attempting to connect to the LDAP service.

The **login_is_role** option when set to ```true``` will use the login username as the only group name when selecting connections.  Standard practice would be to use group names when tying users to connections so this setting should generally be left as the default value of ```false```.

!!! important "Make sure to update connections"
    When using LDAP as an authentication type you **must** add a list of groups to the roles section of the connection objects in order to link the users to which connection(s) they can access.  See the section *Connecting User Groups to Connections* in the [Authentication](connections.md#connecting-user-groups-to-connections) section.

## LDAP Authentication (Microsoft/Active Directory)

Simple example of authenticating through LDAP to Microsoft's Active Directory is shown below:

``` yaml
authenticator:
    type: ldap
    host: your-microsoft-domain-server
    extra_args:
        version: 3
    options:
        use_ssl: true
        login_is_role: false
        base_dn: dc=example,dc=com
        user_search_filter: (&(objectClass=user)(aAMAccountName={USERNAME}))
```

The **login_is_role** option when set to ```true``` will use the login username as the only group name when selecting connections.  Standard practice would be to use group names when tying users to connections so this setting should generally be left as the default value of ```false```.

!!! warning
    When using Active Directory you must sign in using the netbios style format **domain\username**.

!!! important "Make sure to update connections"
    When using LDAP as an authentication type you **must** add a list of groups to the roles section of the connection objects in order to link the users to which connection(s) they can access.  See the *OpenLDAP and Microsoft Active Directory* section in the [Connections](connections.md#openldap-and-microsoft-active-directory) area.

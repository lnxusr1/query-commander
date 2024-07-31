# Authentication

## Local Database Authentication

The most basic method of authentication is to leverage standard local database authentication.  This method asks for the end-users login and password and then uses those credentials directly to log into the database connections configured.

To enable local authentication enter the following in the *settings.yml* file:

``` yaml
authenticator:
  type: local
```
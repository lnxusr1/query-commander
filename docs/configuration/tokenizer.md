# Session Management

Tokens are used to store temporary session-specific information for logged in users.

!!! warning "Cloud Installations"
    Cloud-based installations must use a cloud-compatible session management option.  Local tokens are not supported in cloud-based installations.

# Local Tokens

The most basic method of token storage is to save them in a folder on the local server.  To enable local token storage enter the following in the *settings.yml* file:

``` yaml
tokenizer:
  type: local
  timeout: 20 # minutes
  path: /tmp/tokens
  safe_password: abc123456abcdef
```

!!! note "Set a Strong Safe Password"
    The ```safe_password``` is used to encrypt any local authentication credentials when storing them on the token so be sure to use a strong password.
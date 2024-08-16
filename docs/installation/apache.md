# Apache 2.x (httpd) Installation

!!! important "SSL required"
    The hosting of this service requires SSL to be employed.  Without it several features will not work properly.

!!! note "Don't forget..."
    Make sure to also update your [configuration](../configuration/authenticator.md)

## Setup the Python Runtime Environment

``` bash
apt-get install python3-pip
apt-get install python3-venv

# Setup some empty folders for later
mkdir -p /path/to/query-commander/site
mkdir -p /path/to/query-commander/config

python3 -m venv /path/to/query-commander/.venv
source /path/to/query-commander/.venv/bin/activate
pip install querycommander[all]
```

## Place your index script

``` bash
vi /path/to/query-commander/site/index.py
```

Enter the following text and save the file:

``` python
#!/usr/bin/env python
from querycommander import start
start.as_cgi()
```

Make sure to set the file to executable:

``` bash
chmod a+x /path/to/query-commander/site/index.py
```

Now add your ```settings.yml``` file:

``` bash
vi /path/to/query-commander/config/settings.yml
```

*See the [Configuration](basic.md) section for configuration options.*

## Set up the Apache Virtual Host

Create an Apache configuration file:  

```
sudo vi /etc/apache2/sites-available/your-site-name.conf
```

Example configuration for the virtual host is shown below:

``` apacheconf
<VirtualHost *:443>
    ServerAdmin webmaster@localhost
    ServerName your-site-name.com
    DocumentRoot /path/to/query-commander/site/

    SetEnv QRYCOMM_CONFIG_PATH "/path/to/query-commander/config"

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory "/path/to/query-commander/site/">
        AllowOverride All
        Options FollowSymLinks ExecCGI 
        Require all granted
        AddHandler cgi-script .py

        SetEnv VIRTUAL_ENV "/path/to/query-commander/.venv"
        SetEnv PATH "/path/to/query-commander/.venv/bin:$PATH"
        SetEnv PYTHONPATH "/path/to/query-commander/.venv/lib/python3.11/site-packages"
    </Directory>

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/your-server-ssl.crt
    SSLCertificateKeyFile /etc/ssl/private/your-server-private.key

</VirtualHost>
```

Then enable the site:

``` shell
sudo a2ensite your-site-name
sudo systemctl restart apache2
```

## Connecting to the UI

The Python module is designed to serve the necessary HTML directly from the module so after enabling your site you should be able to browser to the URL that would represent "index.py".  If you've enabled indexes in your Apache configuration you can access it by navigating to the directory that index.py is served under.

In the example configuration above that would equate to:

``` html
https://your-site-name.com/index.py
```

As always, reach out and start a [discussion](https://github.com/lnxusr1/query-commander/discussions) if you need help.

!!! note "Linux Installations"
    These instructions are targeted for Debian-based Linux distributions.  Other distributions may require minor adjustments.  

!!! warning "Microsoft Windows Installations"
    If you are installing on Windows you will at least need to check the header in your ```index.py``` and be sure it points to a valid python interpreter and work your way out from there.  For more specific help then join in the discussion on [GitHub](https://github.com/lnxusr1/query-commander/discussions).

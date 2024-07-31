# Apache 2.x (httpd) Installation

!!! note "Linux Installations"
    These instructions are targeted for Debian-based Linux distributions.  Other distributions may require minor adjustments.  

!!! warning "Microsoft Windows Installations"
    If you are installing on Windows you will at need to check the header in ```query-commander/src/code/index.py``` and be sure it points to a valid python interpreter and work your way out from there.  For more specific help then join in the discussions.

## Setup the Python Runtime Environment

``` shell
apt-get install python3-pip
apt-get install python3-venv

python3 -m venv /path/to/query-commander/.venv
source /path/to/query-commander/.venv/bin/activate
pip install -r /path/to/query-commander/requirements.txt
```

## Set up the Apache Virtual Host

Create a file:  

```
sudo vi /etc/apache2/sites-available/your-site-name.conf
```

Example configuration for the virtual host is shown below:

``` apacheconf
<VirtualHost *:443>
    ServerAdmin webmaster@localhost
    ServerName your-site-name.com
    DocumentRoot /path/to/query-commander/src/static

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory /path/to/query-commander/src/static/>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    Alias /api /path/to/query-commander/src/code/

    <Directory "/path/to/query-commander/src/code/">
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

## Mark all *.py files as executable

``` shell
cd /path/to/query-commander/src/code/
chmod a+x *.py
chmod a+x connectors/*.py
chmod a+x core/*.py
chmod a+x functions/*.py
```

Then be sure to update your [configuration](../../configuration/authenticator/)
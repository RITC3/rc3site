#!/bin/bash

apt-get install python-pip
pip install virtualenv
git clone git@git.havefuninside.me:root/rc3site.git
cd rc3site
virtualenv flask
source flask/bin/activate
for i in ' ' -Mail -Oauthlib -WTF -SQLAlchemy -Login;do pip install Flask$i;done
pip install sqlalchemy-migrate
./db_create.py
echo 'Done!'

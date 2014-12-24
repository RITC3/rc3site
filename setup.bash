#!/bin/bash

apt-get install python-pip
pip install virtualenv
virtualenv flask
source flask/bin/activate
for i in ' ' -Mail -Oauthlib -WTF -SQLAlchemy -Login;do pip install Flask$i;done
pip install sqlalchemy-migrate
./db_create.py
echo 'Done!'

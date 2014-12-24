RC3 Website
===========
Well here it is up on git! Neat!

Setup
-----
Since the site relies on a python virtualenv you cannot just clone it and go...

You'll also need to create a database.

First, you need to set up a new virtualenv for flask and install all of the modules.

This guide assumes you don't have anything except python 2.7 installed and was written for Ubuntu

```
apt-get install python-pip
pip install virtualenv
git clone http://git.havefuninside.me/root/rc3site.git
cd rc3site
virtualenv flask
source flask/bin/activate
for i in ' ' -Mail -Oauthlib -WTF -SQLAlchemy Login;do pip install Flask$i;done
pip install sqlalchemy-migrate
```

Now on to creating the database...

```
rm -rf db_repository app.db
./db_create.py
```

Now we are good to start the server locally with a fresh DB

`python run.py` for debug

`python runp.py` for production

RC3 Website
===========
Well here it is up on git! Neat! Its also messy as shit, but that's okay :)

Setup
-----
Since the site relies on a python virtualenv you have to run the setup script before using it

This guide assumes you don't have anything except python 2.7 installed and was written for Ubuntu

```bash
git clone https://github.com/RITC3/rc3site.git
cd rc3site
pip install virtualenv
virtualenv flask
source flask/bin/activate
pip install -r requirements.txt
```

Now we are good to start the server locally with a fresh DB

`python run.py` for debug

`python runp.py` for production

They both run on port 5000

Credit Where Credit is Due
--------------------------
Original site design/app - Jon Barber

2015 Mainainers/Upgraders - Jaime Geiger/Scott Vincent

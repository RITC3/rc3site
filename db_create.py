#!flask/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import User
from config import BASE_ADMINS, USER_ROLES
import os.path
import sys

if os.path.exists("app.db"):
    if raw_input("DB already exists...\n" \
                 "You can delete it but that will clear all user data\n" \
                 "Are you sure you want to delete it? ").lower() == "y":
        os.remove("app.db")
    else:
        print("Aborting...")
        sys.exit()

db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
	api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
	api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
	api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

print("Finished creating database")

for admin in BASE_ADMINS:
    admin = admin.rstrip()
    print("Adding {} as an an admin".format(admin))
    db.session.add(User(
        nickname = admin.split('@')[0],
        username = admin.split('@')[0],
        email = admin,
        role = USER_ROLES['admin'],
        position = "",
        major = "Security",
        newsletter = 1,
        about_me = ""
    ))
    db.session.commit()

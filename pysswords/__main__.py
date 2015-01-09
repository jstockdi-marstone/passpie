import argparse
from getpass import getpass
import os
import re

from .db import Database, Credential


def default_db():
    return os.path.join(os.path.expanduser("~"), ".pysswords")


def parse_args(cli_args=None):
    parser = argparse.ArgumentParser(prog="Pysswords")

    group_db = parser.add_argument_group("Databse options")
    group_db.add_argument("-I", "--init", action="store_true")
    group_db.add_argument("-D", "--database", default=default_db())

    group_cred = parser.add_argument_group("Credential options")
    group_cred.add_argument("-a", "--add", action="store_true")
    group_cred.add_argument("-g", "--get")
    group_cred.add_argument("-u", "--update")
    group_cred.add_argument("-r", "--remove")
    group_cred.add_argument("-s", "--search")
    group_cred.add_argument("-c", "--clipboard", action="store_true")
    group_cred.add_argument("-P", "--show-password", action="store_true")

    args = parser.parse_args(cli_args)
    if args.clipboard and not args.get:
        parser.error('-g argument is required in when using -c')

    return args


def prompt_password(text):
    for _ in range(3):
        password = getpass(text)
        repeat_password = getpass("Type again: ")
        if password == repeat_password:
            return password
        else:
            print("Entries don't match!")
    else:
        raise ValueError("Entries didn't match")


def prompt(text, default=None, password=False):
    if password:
        prompt_password(text)
    else:
        entry = input("{}{} ".format(
            text,
            "[{}]".format(default) if default else "")
        )
        return entry


def prompt_credential(database, **defaults):
    name = prompt("Name: ", defaults.get("name"))
    login = prompt("Login: ", defaults.get("login"))
    password = prompt("Password: ")
    comment = prompt("Comment: ", defaults.get("comment"))
    return Credential(name, login, database.encrypt(password), comment)


def split_name(fullname):
    rgx = re.compile(r"(?:(?P<login>.+)?@)?(?P<name>[\w\s\._-]+)")
    if rgx.match(fullname):
        name = rgx.match(fullname).group("name")
        login = rgx.match(fullname).group("login")
        return name, login
    else:
        raise ValueError("Not a valid name")


def print_credentials(credentials, show_password=False):
    for credential in credentials:
        credential_str = "{}, {}, {}, {}".format(
            credential.name,
            credential.login,
            credential.password if show_password else "***",
            credential.comment
        )
        print(credential_str)


def print_plaintext(credentials, database, passphrase):
    plaintext_credentials = []
    for c in credentials:
        new_credential = Credential(
            c.name,
            c.login,
            database.decrypt(c.password, passphrase),
            c.comment
        )
        plaintext_credentials.append(new_credential)
    return print_credentials(plaintext_credentials, True)


def main(cli_args=None):
    args = parse_args(cli_args)

    # get database
    if args.init:
        passphrase = prompt("Passhprase for database", password=True)
        database = Database.create(args.database, passphrase)
    else:
        database = Database(path=args.database)

    # updating database
    if args.add:
        credential = prompt_credential(database)
        database.add(credential)

    # selecting
    if args.get:
        name, login = split_name(args.get)
        credentials = database.credential(name=name, login=login)
    else:
        credentials = database.credentials

    # printing
    if args.show_password:
        passphrase = getpass("Passphrase: ")
        if database.check(passphrase):
            print_plaintext(credentials, database, passphrase)
    else:
        print_credentials(credentials)


if __name__ == "__main__":
    main()

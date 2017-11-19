#!/usr/bin/env python2.7

from  controller import Controller
import argparse
import logging
import atexit
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

con = Controller("data/content.db")

def add_user(args):
    logger.debug("Adding user: %s" % args)
    result = con.add_user(args.login,args.name)
    print result
    
def show_user(args):
    logger.debug("Show user:%s" % args)
    result = con.get_user(login=args.login,id=args.id)
    print result
    
def list_user(args):
    logger.debug("List user:%s" % args)
    result = con.list_user()
    print result

def del_user(args):
    logger.debug("Delete user:%s" % args)
    result = con.delete_user(login=args.login,id=args.id)
    print result

def teardown():
    con.close()

if __name__ == "__main__":
    atexit.register(teardown)
    parser = argparse.ArgumentParser(description="Server manager")
    subparsers = parser.add_subparsers(help="manipulate racks,users,servers and instances",dest='action')

    # add-user
    parser_add_user = subparsers.add_parser('add-user', help="add a new user")
    parser_add_user.add_argument("--name", help="name of the user to be added", required=True,type=str)
    parser_add_user.add_argument("--login", help="login of the user to be added", required=True,type=str)
    parser_add_user.set_defaults(func=add_user)

    # show-user
    parser_show_user = subparsers.add_parser('show-user', help="show user")
    group_show_user = parser_show_user.add_mutually_exclusive_group(required=True)
    group_show_user.add_argument("--login", help="login of the user",type=str)
    group_show_user.add_argument("--id", help="id of the user",type=int)
    parser_show_user.set_defaults(func=show_user)

    # del-user
    parser_del_user = subparsers.add_parser('del-user', help="show user")
    group_del_user = parser_del_user.add_mutually_exclusive_group(required=True)
    group_del_user.add_argument("--login", help="login of the user to delete",type=str)
    group_del_user.add_argument("--id", help="id of the user to delete",type=int)
    parser_del_user.set_defaults(func=del_user)

    # list-user
    parser_list_user = subparsers.add_parser('list-user', help="list all users")
    parser_list_user.set_defaults(func=list_user)

   # add-rack
    parser_add_user = subparsers.add_parser('add-user', help="add a new user")
    parser_add_user.add_argument("--name", help="name of the user to be added", required=True,type=str)
    parser_add_user.add_argument("--login", help="login of the user to be added", required=True,type=str)
    parser_add_user.set_defaults(func=add_user)

    # show-rack
    parser_show_user = subparsers.add_parser('show-user', help="show user")
    group_show_user = parser_show_user.add_mutually_exclusive_group(required=True)
    group_show_user.add_argument("--login", help="login of the user",type=str)
    group_show_user.add_argument("--id", help="id of the user",type=int)
    parser_show_user.set_defaults(func=show_user)

    # del-rack
    parser_del_user = subparsers.add_parser('del-user', help="show user")
    group_del_user = parser_del_user.add_mutually_exclusive_group(required=True)
    group_del_user.add_argument("--login", help="login of the user to delete",type=str)
    group_del_user.add_argument("--id", help="id of the user to delete",type=int)
    parser_del_user.set_defaults(func=del_user)

    # list-rack
    parser_list_user = subparsers.add_parser('list-user', help="list all users")
    parser_list_user.set_defaults(func=list_user)
     
    args = parser.parse_args()
    args.func(args)

#!/usr/local/bin/python

import argparse
import logging
import atexit
import traceback
import sys

import config
import controller

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

con = controller.Controller(config.db_path)

entity_column_map = {
   'user': ['id','created_date','login','name','last_updated'],
   'rack': ['id','created_date','name','total_slots','description','last_updated','num_servers'],
   'server': ['id','created_date','rack_id','name','total_cpu','used_cpu','total_memory','used_memory','total_disk','used_disk','description'],
   'instance': ['id','created_date','server_id','owner_id','name','cpu','memory','disk','description','last_updated']
   }

def print_table(myDict, colList=None):
   if not colList: colList = list(list(myDict[0].keys()) if myDict else [])
   myList = [colList] # 1st row = header
   for item in myDict: myList.append([str(item[col] if item[col] is not None else '') for col in colList])
   colSize = [max(list(map(len,col))) for col in zip(*myList)]
   formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
   myList.insert(1, ['-' * i for i in colSize]) # Seperating line
   for item in myList: print((formatStr.format(*item)))

def display_result(records=None,columns=None,header=None,footer=None):
    if header: print(header)
    print_table(records,colList=columns)
    print("\n=============================\n")
    if footer: print(footer)

def manipulate_user(args):
    if args.action == 'add':
        logger.debug("Adding user: %s" % args)
        result = con.add_user(args.login,args.name)
    elif args.action == 'show':
        logger.debug("Show user:%s" % args)
        result = con.get_user(login=args.login,id=args.id)
    elif args.action == 'list':
        logger.debug("List user:%s" % args)
        result = con.list_user()
    elif args.action == 'del':
        logger.debug("Delete user:%s" % args)
        result = con.delete_user(id=args.id,login=args.login)
    if not isinstance(result,list):
       result = [result]
    return result

def manipulate_server(args):
    logger.debug("Manipulating server with input:%s", args)
    if args.action == 'add':
        result = con.add_server(name=args.name,cpu=args.cpu,memory=args.memory,disk=args.disk,rack_id=args.rack_id,rack_name=args.rack_name,desc=args.desc)
    elif args.action == 'show':
        result = con.get_server(id=args.id,name=args.name)
    elif args.action in ('del','delete'):
        result = con.delete_server(id=args.id,name=args.name)
    elif args.action == 'list':
        result = con.list_server()
    if not isinstance(result,list):
       result = [result]
    return result

def manipulate_rack(args):
    logger.debug("Manipulating rack with input:%s", args)
    if args.action == 'add':
        result = con.add_rack(name=args.name,total_slots=args.slots,desc=args.desc)
    elif args.action == 'show':
        result = con.get_rack(id=args.id,name=args.name)
    elif args.action in ('del','delete'):
        result = con.delete_rack(id=args.id,name=args.name)
    elif args.action == 'list':
        result = con.list_rack()
    elif args.action == 'modify':
        mod_args = {k:v for k,v in vars(args).items() if k in ['name','description','total_slots']}
        result = con.modify_rack(id=args.id,**mod_args)
    if not isinstance(result,list):
       result = [result]
 
    return result

def manipulate_instance(args):
    logger.debug("Manipulating instance with input:%s", args)
    if args.action == 'add':
        result = con.add_instance(name=args.name,cpu=args.cpu,memory=args.memory,disk=args.disk,server_id=args.server_id,server_name=args.server_name,desc=args.desc,owner_id=args.owner_id,owner_login=args.owner_login)
    elif args.action == 'show':
        result = con.get_instance(id=args.id,name=args.name)
    elif args.action in ('del','delete'):
        result = con.delete_instance(id=args.id,name=args.name)
    elif args.action == 'list':
        result = con.list_instance()
    elif args.action == 'move':
        result = con.move_instance(id=args.id,name=args.name,dest_server_id=args.dest_server_id,dest_server_name=args.dest_server_name)
    if not isinstance(result,list):
       result = [result]
    return result

def teardown():
    con.close()

if __name__ == "__main__":
    atexit.register(teardown)

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--logging", help="turn on logging",action="store_true")
    parent_parser.add_argument("--debug", help="turn on debug logging",action="store_true")    
    
    parser = argparse.ArgumentParser(description="Server manage",parents=[parent_parser])

    subparsers = parser.add_subparsers(help="manipulate racks,users,servers and instances",dest='entity')

    # USERS
    parser_user = subparsers.add_parser('user', help="manipulate users",parents=[parent_parser])
    subparsers_user = parser_user.add_subparsers(help="add/remove/get/list users",dest='action',title="user actions")
    parser_user.set_defaults(func=manipulate_user)

    # add-user
    parser_add_user = subparsers_user.add_parser('add', help="add a new user",parents=[parent_parser])
    group_add_user = parser_add_user.add_argument_group(title="required args")
    group_add_user.add_argument("--name", help="name of the user to be added", required=True,type=str)
    group_add_user.add_argument("--login", help="login of the user to be added", required=True,type=str)

    # show-user
    parser_show_user = subparsers_user.add_parser('show', help="show user",parents=[parent_parser])
    group_show_user = parser_show_user.add_mutually_exclusive_group(required=True)
    group_show_user.add_argument("--login", help="login of the user",type=str)
    group_show_user.add_argument("--id", help="id of the user",type=int)

    # del-user
    parser_del_user = subparsers_user.add_parser('del', help="delete user",parents=[parent_parser])
    group_del_user = parser_del_user.add_mutually_exclusive_group(required=True)
    group_del_user.add_argument("--login", help="login of the user to delete",type=str)
    group_del_user.add_argument("--id", help="id of the user to delete",type=int)

    # list-user
    parser_list_user = subparsers_user.add_parser('list', help="list all users",parents=[parent_parser])
    parser_list_user.set_defaults(func=manipulate_user)

    # RACK
    parser_rack = subparsers.add_parser('rack', help="manipulate racks",parents=[parent_parser])
    subparsers_rack = parser_rack.add_subparsers(help="manipulate racks", dest='action',title='rack actions')
    parser_rack.set_defaults(func=manipulate_rack)
    # add-rack
    parser_add_rack = subparsers_rack.add_parser('add', help="add a new rack",parents=[parent_parser])
    group_add_rack = parser_add_rack.add_argument_group(title="required args")
    group_add_rack.add_argument("--name", help="name of the rack to be added", required=True,type=str)
    group_add_rack.add_argument("--slots", help="number of slots on the rack", required=True,type=int)
    group_add_rack.add_argument("--desc", help="description of the rack",type=str)

    # modify-rack
    parser_modify_rack = subparsers_rack.add_parser('modify', help="modify a rack by id",parents=[parent_parser])
    group_modify_rack = parser_modify_rack.add_argument_group(title="modify args")
    group_modify_rack.add_argument("--id", help="id of the rack",required=True,type=int)    
    group_modify_rack.add_argument("--name", help="name of the rack to be added", type=str)
    group_modify_rack.add_argument("--slots", help="number of slots on the rack", type=int, dest="total_slots")
    group_modify_rack.add_argument("--desc", help="description of the rack",type=str,dest="description")

    # show-rack
    parser_show_rack = subparsers_rack.add_parser('show', help="show rack",parents=[parent_parser])
    group_show_rack = parser_show_rack.add_mutually_exclusive_group(required=True)
    group_show_rack.add_argument("--id", help="id of the rack",type=int)
    group_show_rack.add_argument("--name", help="name of the rack",type=str)

    # del-rack
    parser_del_rack = subparsers_rack.add_parser('del', help="delete rack",parents=[parent_parser])
    group_del_rack = parser_del_rack.add_mutually_exclusive_group(required=True)
    group_del_rack.add_argument("--id", help="id of the rack to delete",type=int)
    group_del_rack.add_argument("--name", help="name of the rack to delete",type=str)    

    # list-rack
    parser_list_rack = subparsers_rack.add_parser('list', help="list all racks",parents=[parent_parser])

    # SERVER
    parser_server = subparsers.add_parser('server', help="manipulate servers",parents=[parent_parser])
    subparsers_server = parser_server.add_subparsers(help="manipulate servers", dest='action',title='server actions')
    parser_server.set_defaults(func=manipulate_server)

    # add-server
    parser_add_server = subparsers_server.add_parser('add', help="add a new server",parents=[parent_parser])
    group_add_server = parser_add_server.add_argument_group(title="required args")
    group_add_server.add_argument("--name", help="name of the server to be added", required=True,type=str)
    group_add_server.add_argument("--cpu", help="number of cpu the server", required=True,type=int)
    group_add_server.add_argument("--memory", help="available memory in MB", required=True,type=int)
    group_add_server.add_argument("--disk", help="available disk in MB", required=True,type=int)    
    group_add_server.add_argument("--desc", help="description of the server",type=str)
    group_server_rack = group_add_server.add_mutually_exclusive_group(required=True)
    group_server_rack.add_argument("--rack-id", help="id of the rack (or provide rack name)",type=int)
    group_server_rack.add_argument("--rack-name", help="name of the rack (or provide rack id)",type=str)
    
    
    # show-server
    parser_show_server = subparsers_server.add_parser('show', help="show server",parents=[parent_parser])
    group_show_server = parser_show_server.add_mutually_exclusive_group(required=True)
    group_show_server.add_argument("--id", help="id of the server",type=int)
    group_show_server.add_argument("--name", help="name of the server",type=str)

    # del-server
    parser_del_server = subparsers_server.add_parser('del', help="delete server",parents=[parent_parser])
    group_del_server = parser_del_server.add_mutually_exclusive_group(required=True)
    group_del_server.add_argument("--id", help="id of the server to delete",type=int)
    group_del_server.add_argument("--name", help="name of the server to delete",type=str)

    # list-server
    parser_list_server = subparsers_server.add_parser('list', help="list all servers",parents=[parent_parser])
    # instance
    parser_instance = subparsers.add_parser('instance', help="manipulate instances",parents=[parent_parser])
    subparsers_instance = parser_instance.add_subparsers(help="manipulate instances", dest='action',title='instance actions')
    parser_instance.set_defaults(func=manipulate_instance)

    # add-instance
    parser_add_instance = subparsers_instance.add_parser('add', help="add a new instance",parents=[parent_parser])
    parser_add_instance.add_argument("--name", help="name of the instance to be added", required=True,type=str)
    parser_add_instance.add_argument("--cpu", help="number of cpu the instance", required=True,type=int)
    parser_add_instance.add_argument("--memory", help="available memory in MB", required=True,type=int)
    parser_add_instance.add_argument("--disk", help="available disk in MB", required=True,type=int)
    parser_add_instance.add_argument("--desc", help="description of the instance",type=str)
    group_instance_server = parser_add_instance.add_mutually_exclusive_group(required=True)
    group_instance_server.add_argument("--server-id", help="id of the server on which instance should be created",type=int)
    group_instance_server.add_argument("--server-name", help="name of the server on which instance should be created",type=str)
    group_instance_owner = parser_add_instance.add_mutually_exclusive_group(required=True)
    group_instance_owner.add_argument("--owner-id", help="id of the user who owns the instance",type=int)
    group_instance_owner.add_argument("--owner-login", help="login of the on user who owns the instance",type=str)

    # show-instance
    parser_show_instance = subparsers_instance.add_parser('show', help="show instance",parents=[parent_parser])
    group_show_instance = parser_show_instance.add_mutually_exclusive_group(required=True)
    group_show_instance.add_argument("--id", help="id of the instance",type=int)
    group_show_instance.add_argument("--name", help="name of the instance",type=str)

    # del-instance
    parser_del_instance = subparsers_instance.add_parser('del', help="delete instance",parents=[parent_parser])
    group_del_instance = parser_del_instance.add_mutually_exclusive_group(required=True)
    group_del_instance.add_argument("--id", help="id of the instance to delete",type=int)
    group_del_instance.add_argument("--name", help="name of the instance to delete",type=str)

    # move-instance
    parser_move_instance = subparsers_instance.add_parser('move', help="move instance from one server to another",parents=[parent_parser])
    group_move_instance1 = parser_move_instance.add_mutually_exclusive_group(required=True)
    group_move_instance1.add_argument("--id", help="id of the instance to move",type=int)
    group_move_instance1.add_argument("--name", help="name of the instance to move",type=str)
    group_move_instance2 = parser_move_instance.add_mutually_exclusive_group(required=True)
    group_move_instance2.add_argument("--dest-server-id", help="destination server id",type=int)
    group_move_instance2.add_argument("--dest-server-name",help="destination server name",type=str)
    
    # list-instance
    parser_list_instance = subparsers_instance.add_parser('list', help="list all instances",parents=[parent_parser])

    args = parser.parse_args()
    if not args.logging:
        logger.setLevel(logging.NOTSET)
        controller.logger.setLevel(logging.NOTSET)
    try:
        result = args.func(args)
        display_result(result,columns=entity_column_map[args.entity],footer="%s %d %ss" % (args.action,len(result),args.entity))
    except Exception as e:
        print("ERROR:%s" % e)
        if args.debug:
           print(traceback.format_exc(), file=sys.stderr)

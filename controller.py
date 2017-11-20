#!/usr/bin/env python2.7

import sqlite3
from datetime import datetime
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Controller(object):
    """
     Controller class for adding, updating, retrieving and removing objects
    """
    def __init__(self, db_uri):
        self._dbh = None
        self.db_uri = db_uri
        self._entity_table_map = {
                'user': 'users',
                'rack': 'racks',
                'server': 'servers',
                'instance': 'instances'
            }

    @property    
    def dbh(self):
        if self._dbh is None:
            self._dbh = sqlite3.connect(self.db_uri)
            # try enabling foreign keys
            try:
                self._dbh.execute("PRAGMA foreign_keys = ON")
            except:
                logger.warning("Could not enable foreign_keys on db")
                pass
        return self._dbh

    def create_db(self,sql_file):
        with open(sql_file,'r') as fh:
            sql = fh.read()
        c = self.dbh.cursor()
        c.executescript(sql)
        self.dbh.commit()

    def db_select(self,query,args=None):
        logger.debug("Executing query:%s, args:%s", query,str(args))
        c = self.dbh.cursor()
        if args is None: args = tuple()
        result = c.execute(query,args)
        columns = [i[0] for i in  c.description]
        rows = [dict(zip(columns,row)) for row in c.fetchall()]
        logger.debug("%d rows found", len(rows))
        return rows

    def list_user(self,limit=None):
        query = "select u.*,ifnull(i.num_instances,0) as num_instances from users u left join (select owner_id,count(*) as num_instances from instances  group by owner_id) i on i.owner_id=u.id"        
        query = "select * from users"
        return self.db_select(query)

    def get_user(self, id=None, login=None):
        query = None
        if id:
            query = ("select * from users where id=?",(id,))
        elif login:
            query = ("select * from users where login=?",(login,))
        if not query:
            return None
        
        rows = self.db_select(query[0],query[1])
        logger.debug("Found %d users" % len(rows))
        return rows[0] if rows else None

    def delete_user(self,id=None,login=None):
        user = self.get_user(id=id,login=login)
        if not user:
            raise Exception("User not found:%s")
        count_query = "select count(*) as count from instances  where owner_id=?"
        result = self.db_select(count_query, (user['id'],))
        if result[0]['count'] > 0:
            raise Exception("Cannot delete as user owns instances")        
        self.dbh.execute("delete from users where id=?",  (user['id'],))
        self.dbh.commit()
        return user

    def add_user(self,login=None,name=None):
        id = None
        try:
            c = self.dbh.cursor()
            c.execute("INSERT INTO users(login,name,last_updated) values(?,?,?)", (login,name,now()))
            self.dbh.commit()
            id = c.lastrowid
            
        except Exception, e:
            logger.error("Error creating user:%s", e)
            raise e
        return self.get_user(id=id)

    def list_rack(self,limit=None):
        query = "select r.*,ifnull(s.num_servers,0) as num_servers from racks r left join (select rack_id,count(*) as num_servers from servers  group by rack_id) s on s.rack_id=r.id"
        return self.db_select(query)

    def get_rack(self, id=None, name=None):
        if name is not None and id is None:
            id_result=self.db_select("select id from racks where name=?",(name,))
            if not id_result:
                return None
            id = id_result[0]['id']
        query = ("select r.*,ifnull(s.num_servers,0) as num_servers from racks r left join (select rack_id,count(*) as num_servers from servers where rack_id=? group by rack_id) s on s.rack_id=r.id where r.id=?", (id,id))
        rows = self.db_select(query[0],query[1])
        logger.debug("Found %d racks" % len(rows))
        return rows[0] if rows else None

    def add_rack(self,name=None,total_slots=None,desc=None):
        id = None
        try:
            c = self.dbh.cursor()
            c.execute("INSERT INTO racks(name,total_slots,description,last_updated) values(?,?,?,?)", (name,total_slots,desc,now()))
            id = c.lastrowid
            logger.info("Rack created with id:%s" % id)
            self.dbh.commit()
        except Exception, e:
            logger.error("Error creating rack:%s", e)
            raise e
        return self.get_rack(id=id)

    def delete_rack(self,id=None,name=None):
        rack = self.get_rack(id=id,name=name)

        if not rack:
            raise Exception("Rack not found:%s")

        rack_occupancy_query="select count(*) as count from servers where rack_id=?"
        rack_occupancy = self.db_select(rack_occupancy_query,(rack['id'],))
        
        if rack_occupancy[0]['count'] > 0:
            raise Exception("Cannot delete rack as it has %s servers" % rack_occupancy[0]['count'])
        
        self.dbh.execute("delete from racks where id=?",  (rack['id'],))
        self.dbh.commit()

        return rack

    def close(self):
        if self._dbh is not None:
            self.dbh.close()
        self._dbh = None

    def get_server(self, id=None, name=None):
        query = None
        if id:
            query = ("select * from servers where id=?", (id,))
        elif name:
            query = ("select * from servers where name=?",(name,))
        if not query:
            return None
        rows = self.db_select(query[0],query[1])
        logger.debug("Found %d servers" % len(rows))
        return rows[0] if rows else None

    def list_server(self,limit=None):
        query = "select s.*,ifnull(i.num_instances,0) as num_instances from servers s left join (select server_id,count(*) as num_instances from instances  group by server_id) i on s.id=i.server_id"
        return self.db_select(query)

    def add_server(self,name=None,cpu=None,memory=None,disk=None,rack_id=None,rack_name=None,desc=None):
        rack = self.get_rack(id=rack_id,name=rack_name)
        if not rack:
            raise Exception("rack not found")
        rack_occupancy_query="select count(*) as count from servers where rack_id=?"
        rack_occupancy = self.db_select(rack_occupancy_query,(rack['id'],))
        
        if rack_occupancy[0]['count'] >= rack['total_slots']:
            raise Exception("No slots left on the rack with id={id},name={name}".format(**rack))
        
        insert_query = ("insert into servers(rack_id,name,description,total_cpu,total_memory,total_disk,last_updated) VALUES(?,?,?,?,?,?,?)",(rack['id'],name,desc,cpu,memory,disk,now()))
        id = None
        try:
            c = self.dbh.cursor()
            c.execute(insert_query[0],insert_query[1])
            id = c.lastrowid
            self.dbh.commit()

        except Exception, e:
            self.dbh.rollback()
            logger.error("Could not add server to rack")
            raise e        
        return self.get_server(id=id)
        
    def delete_server(self,id=None,name=None):
        server = self.get_server(id=id,name=name)
        if not server:
            raise Exception("Server not found!")
        instance_count_query = "select count(*) as count from instances where server_id=?"
        instance_count = self.db_select(instance_count_query,(id,))
        if instance_count[0]['count'] > 0:
            raise Exception("Cannot delete the server as it has %d instances" % instance_count[0]['count'])
        try:
            del_query = ("delete from servers where id=?",(server['id'],))
            c = self.dbh.cursor()
            c.execute(del_query[0],del_query[1])
            self.dbh.commit()
        except Exception, e:
            self.dbh.rollback()
            logger.error("Error deleting server:%s", e)
            raise Exception("Could not delete server:%s", e)
        return server
        
    def list_instance(self,limit=None):
        query = "select * from instances"
        return self.db_select(query)

    def get_instance(self,id=None,name=None):
        query = None
        if id:
            query = ("select * from instances where id=?", (id,))
        elif name:
            query = ("select * from instances where name=?",(name,))
        if not query:
            return None
        rows = self.db_select(query[0],query[1])
        logger.debug("Found %d instances" % len(rows))
        return rows[0] if rows else None

    def check_server_instance(self,server,cpu=None,memory=None,disk=None):
        reason = []
        avail_cpu = server['total_cpu'] - server['used_cpu']
        avail_mem = server['total_memory'] - server['used_memory']
        avail_disk = server['total_disk'] - server['used_disk']
        if avail_cpu < cpu:
            reason.append("Insuffcient cpu: required=%d,available=%d" % (cpu,avail_cpu))
        if avail_mem < memory:
            reason.append("Insuffcient memory: required=%d,available=%d" % (memory,avail_mem))
        if avail_disk < disk:
            reason.append("Insuffcient disk: required=%d,available=%d" % (disk,avail_disk))
        return reason

    def add_instance(self,name=None,cpu=None,memory=None,disk=None,server_id=None,server_name=None,owner_id=None,owner_login=None,desc=None):
        server = self.get_server(id=server_id,name=server_name)
        if not server:
            raise Exception("server not found")
        owner = self.get_user(id=owner_id,login=owner_login)
        if not owner:
            raise Exception("Owner not found")
        
        #check
        check_result = self.check_server_instance(server,cpu=cpu,memory=memory,disk=disk)
        if check_result:
            raise Exception("Cannot create instance:%s" % ",".join(check_result))
        
        insert_query = ("insert into instances(server_id,name,description,cpu,memory,disk,owner_id,last_updated) VALUES(?,?,?,?,?,?,?,?)",
                        (server['id'],name,desc,cpu,memory,disk,owner['id'],now()))
        update_query = ("update servers set used_cpu=?,used_memory=?,used_disk=?,last_updated=? where id=?",
                        (server['used_cpu']+cpu,
                         server['used_memory']+memory,
                         server['used_disk']+disk,
                         now(),
                         server['id']))
        
        id = None
        try:
            c = self.dbh.cursor()
            c.execute(insert_query[0],insert_query[1])
            id = c.lastrowid
            c.execute(update_query[0],update_query[1])
            self.dbh.commit()
        except Exception, e:
            self.dbh.rollback()
            logger.error("Could not add server to rack")
            raise e
        
        return self.get_instance(id=id)
    
    def delete_instance(self,id=None,name=None):
        instance = self.get_instance(id=id,name=name)
        if not instance:
            raise Exception("instance not found!")
        try:
            server = self.get_server(instance['server_id'])
            del_query = ("delete from instances where id=?",(instance['id'],))
            update_query = ("update servers set used_cpu=?,used_memory=?,used_disk=?,last_updated=? where id=?",
                            (server['used_cpu']-instance['cpu'],
                             server['used_memory']-instance['memory'],
                             server['used_disk']-instance['disk'],
                             now(),
                             server['id']))
            
            c = self.dbh.cursor()
            c.execute(del_query[0],del_query[1])
            c.execute(update_query[0],update_query[1])
            self.dbh.commit()
        except Exception, e:
            self.dbh.rollback()
            logger.error("Error deleting server:%s", e)
            raise Exception("Could not delete server:%s", e)
        return instance

    def move_instance(self,id=None,name=None,dest_server_id=None,dest_server_name=None):
        instance = self.get_instance(id=id,name=name)
        if not instance:
            raise Exception("instance not found!")
        
        src_server = self.get_server(id=instance['server_id'])
        dest_server = self.get_server(id=dest_server_id,name=dest_server_name)
        if not dest_server:
            raise Exception("invalid server id:%s" % dest_server_id)

        if src_server['id'] == dest_server['id']:
            raise Exception("Cannot move instance, source and dest server id are the same")
        #check target
        check_result = self.check_server_instance(dest_server,cpu=instance['cpu'],memory=instance['memory'],disk=instance['disk'])

        if check_result:
            raise Exception("Cannot move instance:%s" % ",".join(check_result))

        try:
            move_query = ("update instances set server_id=?,last_updated=? where id=?",(dest_server['id'],now(),instance['id']))
            
            update_query1 = ("update servers set used_cpu=?,used_memory=?,used_disk=?,last_updated=? where id=?",
                             (src_server['used_cpu']-instance['cpu'],
                              src_server['used_memory']-instance['memory'],
                              src_server['used_disk']-instance['disk'],
                              now(),
                              src_server['id']))
            
            update_query2 = ("update servers set used_cpu=?,used_memory=?,used_disk=?,last_updated=? where id=?",
                             (dest_server['used_cpu']+instance['cpu'],
                              dest_server['used_memory']+instance['memory'],
                              dest_server['used_disk']+instance['disk'],
                              now(),
                              dest_server['id']))
            
            c = self.dbh.cursor()
            c.execute(move_query[0],move_query[1])
            c.execute(update_query1[0],update_query1[1])
            c.execute(update_query2[0],update_query2[1])
            self.dbh.commit()
        except Exception, e:
            raise Exception("Unable to move instance:%s" % instance['id'])
        return self.get_instance(instance['id'])

    def modify_rack(self,id=None,**kwargs):
        rack = self.get_rack(id=id)
        if not rack:
            raise Exception("invalid rack:%s" % id)
        
        editable_fields = ['name','description','total_slots']

        for k in kwargs.keys():
            if k not in editable_fields:
                raise Exception("Invalid field for editing:%s" % k)
        kwargs['last_updated'] = now()    
        update_fields = [k for k,v in kwargs.iteritems() if v is not None]
        if not update_fields:
            raise Exception("Nothing to modify")
        if 'total_slots' in update_fields:
            if kwargs['total_slots'] < rack['num_servers']:
                raise Exception("cannot resize rack to %d slots as it has %d servers" % (kwargs['total_slots'],rack['num_servers']))
                
        query="update racks set %s where id=?" % (",".join(["%s=?" % k for k in update_fields]))
        args = tuple([kwargs[k] for k in update_fields])
        args += (id,)
        try:
            self.dbh.execute(query,args)
            self.dbh.commit()
        except Exception,e:
            raise Exception("Cannot modify rack with id:%s" % id)
        
        print query,args
        return self.get_rack(id)

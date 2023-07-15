from flask import Flask,render_template,request,redirect,url_for

import controller
import config

app=Flask(__name__)
def get_controller():
    return controller.Controller(config.db_path)

@app.route("/")
def index():
    return render_template("index.html")

def get_form_input(key,default=None):
    return request.form.get(key,request.args.get(key,default))

@app.route('/delete/<entity>/<id>',methods=['POST'])
def delete_entity(entity,id):
    id=int(id)
    con = get_controller()
    func = getattr(con,"delete_%s" % entity)
    if not func:
        return render_template("error.html", error="invalid entity:%s" % entity)
    try:
        result = func(id=id)
    except Exception as e:
        return render_template("error.html", error=str(e))
    return redirect(url_for('list_entity',entity=entity))

@app.route("/rack/edit/",methods=["GET","POST"])
def manipulate_rack():
    con = get_controller()
    id = get_form_input('id')
        
    if request.method=='POST':
        name = get_form_input('name')
        name = name if name else None
        slots = get_form_input('total_slots')
        slots = int(slots) if slots else None
        desc = get_form_input('description')
        desc = desc if desc else None
        try:
            if not id:
                print("CREATE NEW", str((id,name,slots,desc)))
                result = con.add_rack(name=name,total_slots=slots,desc=desc)
                id = result['id']
            else:
                result = con.modify_rack(id=id,total_slots=slots,description=desc,name=name)
            con.close()
            return redirect(url_for('manipulate_rack',id=id))
        except Exception as e:
            return render_template("error.html",error=str(e))
    item = con.get_rack(id=id)
    con.close()
    if id and not item:
        return render_template('error.html',error="invalid rack id:%s" % id)

    return render_template("add_modify_rack.html",item=item)

@app.route("/server/edit/",methods=["GET","POST"])
def manipulate_server():
    con = get_controller()
    id = get_form_input('id')
    if request.method=='POST' and not id:
        name = get_form_input('name')
        name = name if name else None
        cpu = get_form_input('cpu')
        cpu = int(cpu) if cpu else None
        memory = get_form_input('memory')
        memory = int(memory) if memory else None
        disk = get_form_input('disk')
        disk = int(disk) if disk else None
        rack_name = get_form_input('rack_name')
        desc = get_form_input('description')
        try:
            if not id:
                #add new
                result = con.add_server(name=name,cpu=cpu,memory=memory,disk=disk,rack_name=rack_name,desc=desc)
                id = result['id']
            else:
                result = None
            return redirect(url_for('manipulate_server',id=id))
        except Exception as e:
            return render_template("error.html", error=str(e))
    item = con.get_server(id=id)
    if not item and id:
        return redirect(url_for('manipulate_server',id=id))
    racks = con.list_rack()
    con.close()
    return render_template("add_modify_server.html",item=item,racks=racks)

@app.route("/instance/edit/",methods=["GET","POST"])
def manipulate_instance():
    con = get_controller()
    id = get_form_input('id')
    action = get_form_input('action')
    if request.method=='POST' and not id:
        name = get_form_input('name')
        name = name if name else None
        server_id = get_form_input('server_id')
        owner_id = get_form_input('owner_id')
        cpu = get_form_input('cpu')
        cpu = int(cpu) if cpu else None
        memory = get_form_input('memory')
        memory = int(memory) if memory else None
        disk = get_form_input('disk')
        disk = int(disk) if disk else None
        rack_name = get_form_input('rack_name')
        owner_login = get_form_input('owner_login')
        desc = get_form_input('description')
        try:
            result = con.add_instance(name=name,cpu=cpu,memory=memory,disk=disk,server_id=server_id,owner_id=owner_id,desc=desc)
            id = result['id']
            return redirect(url_for('manipulate_instance',id=id))
        except Exception as e:
            return render_template("error.html", error=str(e))
    elif request.method=='POST' and id and action == 'move':
        server_id = get_form_input('server_id')
        dest_server_id = get_form_input('dest_server_id')
        try:
            result = con.move_instance(id=id,dest_server_id=dest_server_id)
            return redirect(url_for('manipulate_instance',id=id))
        except Exception as e:
            return render_template("error.html", error=str(e))

    item = con.get_instance(id=id)
    if not item and id:
        return redirect(url_for('manipulate_instance',id=id))
    users = con.list_user()
    servers = con.list_server()
    con.close()
    return render_template("add_modify_instance.html",item=item,users=users,servers=servers,action=action)

@app.route("/user/edit/",methods=["GET","POST"])
def manipulate_user():
    con = get_controller()
    id = get_form_input('id')
    if request.method=='POST' and not id:
        name = get_form_input('name')
        name = name if name else None
        login = get_form_input('login')
        login = login if login else None
        try:
            if not id:
                #add new
                result = con.add_user(name=name,login=login)
                id = result['id']
            else:
                result = None
            con.close()
            return redirect(url_for('manipulate_user',id=id))
        except Exception as e:
            return render_template("error.html", error=str(e))
    item = con.get_user(id=id)
    con.close()
    if not item and id is not None:
        return redirect(url_for('manipulate_user',id=id))

    return render_template("add_modify_user.html",item=item)


@app.route("/<entity>/list/")
def list_entity(entity):
    con = get_controller()
    func = getattr(con,"list_%s" % entity)
    if not func:
        render_template("error.html", error="invalid entity:%s" % entity)
    result = func()
    if entity=='instance':
        for item in result:
            item['owner'] = con.get_user(item['owner_id'])
    con.close()
    return render_template("%s.html" % entity ,items=result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)

#!/usr/bin/env python2.7

from flask import Flask

import controller
import config

app=Flask(__name__)
def get_controller():
    return controller.Controller(config.db_path)

app.route("/rack/<id>/")
def show_rack(id):
    con = get_controller()
    result = con.get_rack(id=id)
    return str(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8000")

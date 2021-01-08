# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) Stephane Wirtel
# Copyright (C) 2011 Nicolas Vanhoren
# Copyright (C) 2011 OpenERP s.a. (<http://openerp.com>).
# Copyright (C) 2017 Nicolas Seinlet
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
##############################################################################
import odoolib
import time
import sys
import os

from locust import User, events


def send(self, service_name, method, *args):
    if service_name == "object" and method == "execute_kw":
        call_name = "%s : %s" % args[3:5]
    else:
        call_name = '%s : %s' % (service_name, method)
    start_time = time.time()
    try:
        res = odoolib.json_rpc(self.url, "call", {"service": service_name, "method": method, "args": args})
    except Exception as e:
        total_time = int((time.time() - start_time) * 1000)
        events.request_failure.fire(request_type="Odoo JsonRPC", name=call_name, response_time=total_time, exception=e, response_length=total_time)
        raise e
    else:
        total_time = int((time.time() - start_time) * 1000)
        events.request_success.fire(request_type="Odoo JsonRPC", name=call_name, response_time=total_time, response_length=sys.getsizeof(res))
    return res


odoolib.JsonRPCConnector.send = send
odoolib.JsonRPCSConnector.send = send


class OdooUser(User):

    host = os.environ.get("OL_HOST", "127.0.0.1")
    port = os.environ.get("OL_PORT", 8069)
    database = os.environ.get("OL_DB_NAME", "demo")
    login = os.environ.get("OL_LOGIN", "admin")
    password = os.environ.get("OL_PASSWORD", "admin")
    protocol = os.environ.get("OL_PROTOCOL", "jsonrpc")
    user_id = os.environ.get("OL_USER_ID", -1)

    def __init__(self, *args, **kwargs):
        super(OdooUser, self).__init__(*args, **kwargs)
        self._connect()

    def _connect(self):
        user_id = None
        if self.user_id and self.user_id > 0:
            user_id = self.user_id
        self.client = odoolib.get_connection(hostname=self.host,
                                             port=self.port,
                                             database=self.database,
                                             login=self.login,
                                             password=self.password,
                                             protocol=self.protocol,
                                             user_id=user_id)
        self.client.check_login(force=False)
    
    def _get_user_context(self):
        res = self.client.get_model('res.users').read(self.client.user_id, ['lang', 'tz'])
        return {
            'uid': self.client.user_id,
            'lang': res['lang'],
            'tz': res['tz'],
        }

    def _fields_view_get(self, model, view_mode):
        res = self.client.get_model(model).load_views(views=[(False, vm) for vm in list(set(["list", "form", "search", view_mode]))])
        return [n for n in res.get('fields_views', {}).get(view_mode, {}).get('fields', {}).keys()]

    def _filters_view_get(self, model):
        res = self.client.get_model(model).load_views(views=[(False, vm) for vm in list(set(["list", "form", "search"]))])
        return [n['domain'] for n in res.get('filters', {})]

    def _parse_children_menu(self, childs):
        res = []
        for child in childs:
            if child['action']:
                res.append(child['action'].split(","))
            if child['children']:
                res += self._parse_children_menu(child['children'])
        return res

    def _load_menu(self):
        res = self.client.get_model('ir.ui.menu').load_menus(False, context=self._get_user_context())
        return self._parse_children_menu(res['children'])

    def _action_load(self, action_id, action_type=None):
        if not action_type:
            base_action = self.client.get_model('ir.actions.actions').read(action_id, ['type'])
            action_type = base_action[0]['type']
        return self.client.get_model(action_type).read(action_id, [])

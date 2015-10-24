from jinja2 import Template, Environment, PackageLoader, FileSystemLoader
from urllib.parse import parse_qs
import urllib.parse
from pymongo import MongoClient, ASCENDING, DESCENDING
import bson
import http.cookies
import hashlib
import os


def application(env, start_response):
	env1 = Environment(loader = FileSystemLoader('temp'))
	c = http.cookies.SimpleCookie()
	if 'HTTP_COOKIE' in env:
		c = http.cookies.SimpleCookie(env['HTTP_COOKIE'])

	# журнальный инстанс
	jclient = MongoClient("mongodb://{0}:27017".format(os.environ["HS_MONGO_JOURNAL_PORT_27017_TCP_ADDR"]))

	# инстанс с данными
	client = MongoClient("mongodb://{0}:27017".format(os.environ["HS_MONGO_DATA_PORT_27017_TCP_ADDR"]))

	if 'user' not in c:
		try:
			request_body_size = int(env.get('CONTENT_LENGTH', 0))
		except (ValueError):
			request_body_size = 0
		query = dict()
		if request_body_size != 0:
			qs = urllib.parse.unquote(env['wsgi.input'].read(request_body_size).decode('ascii'))
			query = parse_qs(qs)
		if env['PATH_INFO'] == "/register/" or env['PATH_INFO'] == "/register":
			import register
			return register.reg(env, start_response, query)
		elif "login" in query:
			import auth
			return auth.auth(env, start_response, query)

		template = env1.get_template("auth.html")
		resp = template.render()
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [resp.encode('utf-8')]
	else:
		db = jclient[c["user"].value]
		collection = db.task
		collection_info = db["meta"]
		info = collection_info.find_one()
		if 'meta' in db.collection_names() and hashlib.md5(info["password"].encode('utf-8')).hexdigest() == c["secret"].value:
			try:
				request_body_size = int(env.get('CONTENT_LENGTH', 0))
			except (ValueError):
				request_body_size = 0
			qs = str()
			query = dict()
			if request_body_size > 0:
				qs = urllib.parse.unquote(env['wsgi.input'].read(request_body_size).decode('ascii'))
			elif len(env['QUERY_STRING']) > 0:
				qs = env['QUERY_STRING']
			resp = ""
			if len(qs):
				query = parse_qs(qs)
			if len(qs) and "jshow" not in query:
				if 'exit' not in query:
					if query["act"][0] == "add":
						import time
						import json

						start_response('200 OK', [('Content-Type', 'application/json')])

						limmit = 5
						groups = client[c["user"].value].collection_names(False)
						if len(groups) >= limmit:
							return [json.dumps({"status": "500", "error_text": "Превышен лиммит количества групп"}).encode('utf-8')]
						if "meta" not in jclient[c["user"].value].collection_names():
							return [json.dumps({"status": "500", "error_text": "wrong user"}).encode('utf-8')]

						import vkreq

						resp_vk = vkreq.get_group(query["groupid"][0])
						if "error" in resp_vk:
							return [json.dumps({"status": "500", "error_text": "wrong gid"}).encode('utf-8')]

						str_gid = str(resp_vk["response"][0]["gid"])
						if str_gid in client[c["user"].value].collection_names():
							return [json.dumps({"status": "500", "error_text": "Группа уже была добавленна раньше"}).encode('utf-8')]

						if "meta" not in jclient[str_gid].collection_names():
							jclient[str_gid]["meta"].insert_one(resp_vk["response"][0])

						import rmqsend
						rmqsend.send(json.dumps({"user": c["user"].value, "group_id": str_gid}).encode('utf-8'))

						return [json.dumps({"status": "200"}).encode('utf-8')]
					elif query["act"][0] == "update":
						import json
						last_doc_journal = jclient[c["user"].value]["journal"].find_one({"gid": query["gid"][0]}, sort = [("ts", DESCENDING)])
						import time

						# Ограничение на частоту запросов на обновление
						rest = 1800
						start_response('200 OK', [('Content-Type', 'application/json')])
						if last_doc_journal is not None and (int(time.time()) - last_doc_journal["ts"]) < rest:
							return [
								json.dumps({"status": "500", "error_test": "Превышен лиммит на количество запросов на обновление"}).encode('utf-8')]
						import rmqsend
						rmqsend.send(json.dumps({"user": c["user"].value, "group_id": query["gid"][0]}).encode('utf-8'))
						return [json.dumps({"status": "200"}).encode('utf-8')]
					else:
						collection.update_one({"_id": bson.objectid.ObjectId(query["id"][0])}, {'$set': {'act': query['act']}})
						start_response('200 OK', [('Content-Type', 'application/json')])
						import json

						return [json.dumps({"status": "200", "act": query["act"][0]}).encode('utf-8')]
				elif "exit" in query:
					c["user"]["Expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"
					c["secret"]["Expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"
					template = env1.get_template("auth.html")
					resp = template.render()
			else:
				usermeta = collection_info.find_one()
				groups = client[c["user"].value].collection_names(False)
				usermeta["groups"] = []
				for i in groups:
					usermeta["groups"].append(jclient[i]["meta"].find_one())
					usermeta["groups"][len(usermeta["groups"]) - 1]["journal"] = []
					for doc in jclient[c["user"].value]["journal"].find({"gid": str(i)}).sort([("ts", DESCENDING)]):
						doc["ts"] = str(doc["ts"])
						usermeta["groups"][len(usermeta["groups"]) - 1]["journal"].append(doc)
					if "jshow" in query and str(i) in query["jshow"]:
						usermeta["groups"][len(usermeta["groups"]) - 1]["jshow"] = "y"
					else:
						usermeta["groups"][len(usermeta["groups"]) - 1]["jshow"] = "n"
				template = env1.get_template("index.html")
				resp = template.render(user = usermeta)
		else:
			if 'user' not in c:
				c['user'] = dict()
			c["user"]["Expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"
			if 'secret' not in c:
				c['secret'] = dict()
			c["secret"]["Expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"
			template = env1.get_template("auth.html")
			resp = template.render()

		start_response('200 OK',
					   [('Content-Type', 'text/html'), ('Set-Cookie', c["user"].OutputString()), ('Set-Cookie', c["secret"].OutputString())])
		return [resp.encode('utf-8')]
	# -L/home/ssi/Downloads/ngx_openresty-1.9.3.1/build/luajit-root/usr/local/openresty/luajit/lib -Wl,-rpath,/usr/local/openresty/luajit/lib -Wl,-E -lpthread -lcrypt -L/home/ssi/Downloads/ngx_openresty-1.9.3.1/build/luajit-root/usr/local/openresty/luajit/lib -lluajit-5.1 -lm -ldl -lpcre -lssl -lcrypto -ldl -lz

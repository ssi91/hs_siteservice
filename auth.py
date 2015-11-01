from jinja2 import Template, Environment, PackageLoader, FileSystemLoader
import hashlib
from pymongo import MongoClient, ASCENDING, DESCENDING
import os


def auth(env, start_response, query):
	env1 = Environment(loader = FileSystemLoader('temp'))

	# журнальный инстанс
	jclient = MongoClient("mongodb://{0}:27017".format(os.environ["HS_MONGO_JOURNAL_PORT_27017_TCP_ADDR"]))

	start_response('200 OK', [('Content-Type', 'application/json')])
	import json

	if "." in query["login"][0] or query["login"][0].isdigit():
		return [json.dumps({"status": "500", "error_text": "Неверный логин"}).encode('utf-8')]
	db = jclient[query["login"][0]]
	if "meta" not in db.collection_names():
		return [json.dumps({"status": "500", "error_text": "Неверный логин"}).encode('utf-8')]
	collection_info = db["meta"]
	info = collection_info.find_one()
	hp = hashlib.md5(query["password"][0].encode('utf-8')).hexdigest()
	if info["password"] == hp:
		return [json.dumps({"status": "200", "user": info["user"], "secret": hashlib.md5(hp.encode('utf-8')).hexdigest()}).encode('utf-8')]
	else:
		return [json.dumps({"status": "500", "error_text": "Неверный пароль"}).encode('utf-8')]

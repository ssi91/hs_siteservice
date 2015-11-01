from jinja2 import Template, Environment, PackageLoader, FileSystemLoader
import hashlib
from pymongo import MongoClient, ASCENDING, DESCENDING
import os

"""
2. Проверить e-mail на валидность
3. уведомить об удачной регистрации
"""


def reg(env, start_response, query):
	env1 = Environment(loader = FileSystemLoader('temp'))
	# журнальный инстанс
	jclient = MongoClient("mongodb://{0}:27017".format(os.environ["HS_MONGO_JOURNAL_PORT_27017_TCP_ADDR"]))

	try:
		request_body_size = int(env.get('CONTENT_LENGTH', 0))
	except (ValueError):
		request_body_size = 0

	import json
	if request_body_size > 0:
		start_response('200 OK', [('Content-Type', 'application/json')])
		if "." in query["login"][0]:
			return [json.dumps({"status": "500", "error_text": "Недопустимые символы в логине"}).encode('utf-8')]
		elif query["login"][0].isdigit():
			return [json.dumps({"status": "500", "error_text": "Логин не может состоять только из цифр"}).encode('utf-8')]

		# Проверка валидность E-mail
		import re
		email_re = re.compile(
			r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
			r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
			r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$'
			, re.IGNORECASE)
		valid_email = re.search(email_re, query["email"][0])
		if valid_email is None:
			return [json.dumps({"status": "500", "error_text": "E-mail не валидный"}).encode('utf-8')]

		# Если тут всё ОК, проверяем на наличие пользователя с таким логином. Если такого нет, добавляем
		mq = dict()
		db = jclient[query["login"][0]]
		if "meta" not in db.collection_names():
			collection = db["meta"]
			mq["user"] = query["login"][0]
			mq["email"] = query["email"][0]
			hp = hashlib.md5(query["password"][0].encode('utf-8')).hexdigest()
			mq["password"] = hp
			mq["money"] = 0
			collection.insert_one(mq)  # TODO добавить проверки на сложность пароля
			return [json.dumps({"status": "200"}).encode('utf-8')]
		else:
			return [json.dumps({"status": "500", "error_text": "Такой пользователь уже есть"}).encode('utf-8')]

	template = env1.get_template("register.html")
	resp = template.render()
	start_response('200 OK', [('Content-Type', 'text/html')])
	return [resp.encode('utf-8')]

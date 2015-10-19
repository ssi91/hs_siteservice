import urllib.request
import json


def get_group(id):
	r = urllib.request.urlopen('https://api.vk.com/method/groups.getById?group_id={0}'.format(id))
	dr = json.JSONDecoder().decode(r.read().decode("utf-8"))
	return dr

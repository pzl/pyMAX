import os
import time
from pathlib import Path
import requests
import json


URL_BASE = "https://app.childcarecentersoftware.com/api"
API_BASE = URL_BASE + "/rosella/v1"

token = None

def request(route,method='GET',params=None,data=None):
	global token

	authHeader = {"Authorization": f"Bearer {token['access_token']}"}

	if not params:
		params={}
	if not data:
		data = {}

	method = method.lower()

	if method == "post":
		req = requests.post
	elif method == "put":
		req = requests.put
	elif method == "delete":
		req = requests.delete
	else:
		req = requests.get

	r = req(API_BASE + route, params=params, data=data, headers=authHeader)
	return r.json()


def connect(username=None,password=None,token_file=None):
	global token

	token_file = token_file_path(token_file)
	if token_file.exists():
		contents = token_file.read_text()
		if contents:
			token = json.loads(contents)
			if token['created_at'] + token['expires_in'] > time.time():
				return
			else:
				token = refresh(token_file)
				if not 'error' in token:
					return
				else:
					print("Error refreshing token: %s",(token,))

	if not username or not password:
		raise PasswordRequired("could not find a valid token, username and password must be provided")
	token = authenticate(username,password,token_file)
	return token


def token_file_path(fp=None):
	if not fp:
		base = Path(os.getenv("XDG_DATA_HOME","~/.local/share"))
		fp = base / "pyMAX" / "token.json"
	token_file = Path(fp).expanduser()
	token_file.parent.mkdir(parents=True,exist_ok=True)

	return token_file

def authenticate(username,password,token_file=None):
	r = requests.post(URL_BASE + '/oauth/token',data={"username":username,"password":password,"grant_type":"password"})
	j = r.json()

	if not 'error' in j:
		with open(token_file_path(token_file),"w") as f:
			json.dump(j,f)

	return j

def refresh(token_file):
	with open(token_file_path(token_file)) as f:
		token = json.load(f)

	r = requests.post(URL_BASE + '/oauth/token',data={"refresh_token":token['refresh_token'],"grant_type":"refresh_token"})
	j = r.json()

	if not 'error' in j:
		with open(token_file_path(token_file),"w") as f:
			json.dump(j,f)
	return j

class PasswordRequired(Exception):
	pass

# reads credentials from settings.txt and returns a dict with the values
def initLogin():
	credentials = {'username': '',
				   'password1': '',
				   'password2': ''}

	with open("settings.txt", "r") as f:
		pairs = [x.rstrip().split("=") for x in f.readlines()]
		for key,value in pairs:
			credentials[key] = value

	return credentials


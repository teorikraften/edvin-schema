from bs4 import BeautifulSoup
import requests
import arrow
import os
from ics import Calendar, Event
from authFunctions import initLogin


credentials = initLogin()
username = credentials['username']
passwordFirst = credentials['password1']
passwordSecond = credentials['password2']


# 1st login #
url = "https://adfs.sas.dk/adfs/ls"

querystring = {"version":"1.0","action":"signin","realm":"urn:AppProxy:com","appRealm":"4183fd8d-a629-e711-80ea-00155d415332","returnUrl":"https://webroster-tcs.scandinavian.net/webroster-presentation-arn/faces/userHolidayPlanMessages.tiles","client-request-id":"6D006111-17E2-0006-BC75-7171057ED401"}

payload = "AuthMethod=FormsAuthentication&Password={0}&UserName=SAS%5C{1}".format(passwordFirst,username)
headers = {
    'Content-Type': "application/x-www-form-urlencoded",
    }

print("1st login...")
session =  requests.Session()
response = session.request("POST", url, data=payload, headers=headers, params=querystring)
print("Complete!")

# save the required cookies for next login step #
EdgeAccessCookie = response.cookies['EdgeAccessCookie']
JSESSIONID = response.cookies['JSESSIONID']
print("EdgeAccessCookie={0};\nJSESSIONID={1}".format(EdgeAccessCookie, JSESSIONID))

# 2nd login #
url = "https://webroster-tcs.scandinavian.net/webroster-presentation-arn/faces/userHolidayPlanMessages.tiles"

# form data for login #
payload = {"jsf_sequence": "1", 
		   "frmLogin_SUBMIT": "1",
		   "frmLogin:_link_hidden_": "1",
		   "frmLogin:loginButtonId": "Login",
		   "input_for_enterkey_submit": "",
		   "frmLogin:password": passwordSecond,
		   "frmLogin:username": "87782"}

# form data used for navigation #
menuPayload = {"menuFormId_SUBMIT": "1", 
		   	   "menuFormId:_link_hidden_": "menuFormId_mainMenuNav_item1",
		   	   "jsf_sequence": "1"}
headers = {'Cookie': "EdgeAccessCookie=" + EdgeAccessCookie + "; JSESSIONID=" + JSESSIONID}

print("2nd login...")
session.request("POST", url, data=payload, headers=headers)
response = session.request("POST", url, data=menuPayload, headers=headers)
print("Complete!")
session.close()

print("Parsing...")
# parse the data #
soup = BeautifulSoup(response.content, "lxml")

cal = Calendar()

columns = {'personalRosterDate': "",
			'personalRosterWeekDay': "",
			'personalRosterShiftLabel': "",
			'personalRosterShiftDescription': "",
			'personalRosterShiftTimes': "",
			'personalRosterDutyTime': ""}
for row in soup.find("table", class_="dataTable").find_all("tr", {'class':["dataTableOddRow", "dataTableEvenRow"]}):
	for key,_ in columns.items():
		val = row.find("div", class_=key)
		if val:
			columns[key] = val.text
		else:
			columns[key] = ""
	if columns['personalRosterShiftTimes']:
		date = columns['personalRosterDate'].strip() if columns['personalRosterDate'] else date
		times = columns['personalRosterShiftTimes'].split(" - ")
		for i,time in enumerate(times):
			if time == "00:00":
				times[i] = "23:59"
		# add event data to calendar #
		e = Event()
		e.name = columns['personalRosterShiftLabel']
		e.description = columns['personalRosterShiftDescription']
		e.begin = arrow.get(date + times[0], "YYYY-MM-DD HH:mm").replace(tzinfo="Europe/Stockholm")
		e.end = arrow.get(date + times[1], "YYYY-MM-DD HH:mm").replace(tzinfo="Europe/Stockholm")
		cal.events.add(e)

with open("test.ics", 'w') as f:
	f.writelines(cal)
print("Complete! iCal-file written to {0}".format(os.path.realpath(f.name)))

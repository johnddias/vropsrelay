from flask import Flask, Markup, request, json, Response, jsonify
import requests
import logging
import re
import sys
import time

token = ""
user = "admin"
passwd = "VMware1!"
host = "10.140.50.30"

# Define if you want to leverage SSL
SSLCERT = ''
SSLKEY = ''


app = Flask(__name__)

def GetToken(user, passwd, host):
    if not token:
        url = "https://" + host + "/suite-api/api/auth/token/acquire"
        payload = "{\r\n  \"username\" : \"" + user + "\",\r\n  \"authSource\" : \"local\",\r\n  \"password\" : \"" + passwd + "\",\r\n  \"others\" : [ ],\r\n  \"otherAttributes\" : {\r\n  }\r\n}"
        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            }
        response = requests.request("POST", url, data=payload, headers=headers, verify=0)
        return response.text
    elif int(token["validity"])/1000 < time.time():
        url = "https://" + host + "/suite-api/api/versions"
        headers = {
            'authorization': "vRealizeOpsToken " + token["token"],
            'accept': "application/json"
        }
        response = requests.request("GET", url, headers=headers, verify=0)
        if response.status_code == 401:
            url = "https://" + host + "/suite-api/api/auth/token/acquire"
            payload = "{\r\n  \"username\" : \"" + user + "\",\r\n  \"authSource\" : \"local\",\r\n  \"password\" : \"" + passwd + "\",\r\n  \"others\" : [ ],\r\n  \"otherAttributes\" : {\r\n  }\r\n}"
            headers = {
            'accept': "application/json",
            'content-type': "application/json",
            }
            response = requests.request("POST", url, data=payload, headers=headers, verify=0)
            return response.text
        else:
            return json.dumps(token)
    else:
        return json.dumps(token)

def GetResourceStatus(name,host):
    global token
    token = json.loads(GetToken(user, passwd, host))
    url = "https://" + host + "/suite-api/api/resources"

    querystring = {"name": name}

    headers = {
        'authorization': "vRealizeOpsToken " + token["token"],
        'accept': "application/json",
        }

    response = requests.request("GET", url, headers=headers, params=querystring, verify=0)
    response_parsed = json.loads(response.text)
    return response_parsed

def GetActiveAlerts(badge,reskind,host):
    global token
    print token
    token = json.loads(GetToken(user,passwd,host))
    url = "https://" + host + "/suite-api/api/alerts/query"

    headers = {
        'authorization': "vRealizeOpsToken " + token["token"],
        'accept': "application/json",
        'content-type': "application/json"
    }

    querypayload = {
        'resource-query': {
            'resourceKind': [reskind]
        },
        'activeOnly': True,
        'alertCriticality': ["CRITICAL","IMMEDIATE","WARNING","INFORMATION"],
        'alertImpact': [badge]
    }

    response = requests.request("POST", url, headers=headers, json=querypayload, verify=0)
    response_parsed = json.loads(response.text)
    return response_parsed

@app.route("/<NAME>", methods=['GET'])
def ResourceStatusReport(NAME=None):
    statusInfo = GetResourceStatus(NAME,host)
    resp = jsonify(**statusInfo), 200
    return(resp)

@app.route("/alerts/<BADGE>/<RESOURCEKIND>", methods=['GET'])
def ActiveAlertsQuery(BADGE=None, RESOURCEKIND=None):
    alertsQuery = GetActiveAlerts(BADGE,RESOURCEKIND,host)
    resp = jsonify(**alertsQuery), 200
    return(resp)

def main(PORT):
    # Configure logging - overwrite on every start
    logging.basicConfig(filename='vropsrelay.log', filemode='w', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    # stdout
    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    logging.info("Please navigate to the below URL for the available routes")

    if (SSLCERT and SSLKEY):
        context = (SSLCERT, SSLKEY)
        app.run(host='0.0.0.0', port=PORT, ssl_context=context, threaded=True, debug=True)
    else:
        app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    PORT = 5001
    if (len(sys.argv) == 2):
        PORT = sys.argv[1]
    main(PORT)

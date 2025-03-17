import kopf
import subprocess
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml

def bootstrap():
    print("bootstrapping")
    subprocess.run(["flux", "install"])    
    bootstrap_token = install_gitea()
    flux_bootstrap(bootstrap_token)
    # install bigbang
    subprocess.run([f"{BBCTL_BINARY}", "deploy", "bigbang"]) 

print("=========================")
print("--- Big Bang Operator ---")
print("=========================")

GITEA_NAMESPACE = "default"
BIGBANG_OPERATOR_NAMESPACE="default"

# running resources | running applications in namespaces | cluster load | available cloud resources | cluster type
# the information can then be used to either optimize the bigbang install, be opinionated about resource settings, handle upgrades etc. very powerful.

# example:
node_name = subprocess.check_output(["kubectl", "get", "pod", "-l", "app=operate", "-o", "jsonpath='{.items[0].spec.nodeName}'"]).decode('utf-8').strip("'")
node_data = subprocess.check_output(["kubectl", "describe", "node", f"{node_name}"]).decode('utf-8')
for line in node_data.split('\n'):
    if "Architecture" in line:
        if 'amd64' in line:
            arch = 'amd64'
            bbctl_binary ='bbctl'
        if 'arm64' in line:
            arch = 'arm64'
            bbctl_binary ='bbctl-arm64'
if 'arch' not in locals():
    raise Exception("unknown architecture")

ARCHITECUTRE = arch
BBCTL_BINARY = bbctl_binary
print(f"Architecture: {ARCHITECUTRE}")
print(f"BBCTL_BINARY: {BBCTL_BINARY}")

# check if bb is already installed
status = subprocess.check_output([f"{BBCTL_BINARY}", "status"])
if 'No Big Bang release was found.' in status.decode('utf-8'):
    print("bigbang not installed")
    bootstrap()
else:
    print("bigbang already installed")   

def install_gitea():
    print("installing gitea")
    subprocess.run(["helm", "repo", "add", "gitea-charts", "https://dl.gitea.com/charts/"])
    subprocess.run(["helm", "install", "-n", f"{GITEA_NAMESPACE}", "gitea", "gitea-charts/gitea", "-f", "/src/operate/gitea/values.yaml", "--wait"])
    gitea_svc_endpoint = f"http://gitea-http.{GITEA_NAMESPACE}.svc.cluster.local:3000"
    url = f"{gitea_svc_endpoint}/api/v1/users/admin/tokens"
    headers = {"Content-Type": "application/json"}
    data = {
        "name": "bootstrap-token",
        "scopes": [
            "read:repository",
            "write:repository",
            "write:user",
        ]
    }
    auth = HTTPBasicAuth('admin', 'adminpassword')
    response = requests.post(url, headers=headers, json=data, auth=auth)
    print(response.json())
    try:
        bootstrap_token = response.json()['sha1']
    except:
        print("error getting bootstrap token")
        print(response.text)
        raise Exception("error getting bootstrap token")

    # create a gitops project for flux bootstrapping
    url = f"{gitea_svc_endpoint}/api/v1/user/repos"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bootstrap_token}"}
    data = {
        "name": "flux",
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.json())

    return bootstrap_token

def flux_bootstrap(bootstrap_token: str):
    subprocess.run(["flux", "bootstrap", "git", "--url", f"http://gitea-http.{GITEA_NAMESPACE}.svc.cluster.local:3000/admin/flux.git", "--username=admin", f"--password={bootstrap_token}", "--allow-insecure-http=true", "--token-auth=true", "--branch=main"])    


# for now these just run status commands on create and update of BigBang resource
@kopf.on.create('bigbang')
def create_bigbang(spec, name, meta, status, **kwargs):
    
    subprocess.run([f"{BBCTL_BINARY}", "status"])

@kopf.on.update('bigbang')
def upgrade_bigbang(spec, name, meta, status, **kwargs):

    subprocess.run([f"{BBCTL_BINARY}", "status"])


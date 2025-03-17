import kopf
import subprocess
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml


print("running")
GITEA_NAMESPACE = "default"
BIGBANG_OPERATOR_NAMESPACE="default"

def main():
    install_flux()
    bootstrap_token = install_gitea()
    flux_bootstrap(bootstrap_token)
    # need something like if secret exists then use it to flux_bootstrap otherwise continue? also cant remove gitea obvi
    # subprocess.run(["kubectl", "create", "secret", "generic", "--from-literal", f"bootstrap-token={bootstrap_token}", "-n", f"{BIGBANG_OPERATOR_NAMESPACE}", "bootstrap-token"])
    
def install_flux():
    subprocess.run(["flux", "install"])

def install_gitea():
    
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

@kopf.on.create('bigbang')
def install_bigbang(spec, name, meta, status, **kwargs):
    print("[INFO] BigBang resources created! running bbctl")
    # we can do tons of stuff here and above in the deployment for example we can grab all sorts of information like:
    # running resources | running applications in namespaces | cluster load | available cloud resources | cluster type

    # the information can then be used to either optimize the bigbang install, be opinionated about resource settings, handle upgrades etc. very powerful.

    # example:
    node_name = subprocess.check_output(["kubectl", "get", "pod", "-l", "app=operate", "-o", "jsonpath='{.items[0].spec.nodeName}'"]).decode('utf-8').strip("'")
    node_data = subprocess.check_output(["kubectl", "describe", "node", f"{node_name}"]).decode('utf-8')
    for line in node_data.split('\n'):
        if "Architecture" in line:
            if 'amd64' in line:
                arch = 'amd64'
            if 'arm64' in line:
                arch = 'arm64'
    if arch not in locals():
        raise Exception("unknown architecture")

    if arch == 'arm64':
        subprocess.run(["bbctl-arm64", "preflight-check"])
        subprocess.run(["bbctl-arm64", "deploy", "bigbang"])
    if arch == 'amd64':
        subprocess.run(["bbctl", "preflight-check"])
        subprocess.run(["bbctl", "deploy", "bigbang"])

main()

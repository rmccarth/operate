import kopf
import subprocess

print("running")

@kopf.on.create('bigbang')
def install_flux(spec, name, meta, status, **kwargs):
    print("bigbang resources created! installing flux")
    subprocess.run(["kubectl", "apply", "-f", "https://github.com/fluxcd/flux2/releases/latest/download/install.yaml"])

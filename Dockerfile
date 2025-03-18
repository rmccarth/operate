FROM python:3.12
COPY . /src

ENV PYTHONUNBUFFERED=1

# kopf
RUN pip install kopf requests 
# kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && mv kubectl /usr/local/bin/kubectl
# flux
RUN curl -s https://fluxcd.io/install.sh | bash
# helm
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && chmod 700 get_helm.sh && ./get_helm.sh
# bbctl
RUN curl -Ls https://repo1.dso.mil/big-bang/apps/developer-tools/bbctl/-/releases/1.0.0/downloads/bbctl-1.0.0-linux-arm64.tar.gz | tar -xz && mv bbctl /usr/bin/bbctl-arm64
RUN curl -Ls https://repo1.dso.mil/big-bang/apps/developer-tools/bbctl/-/releases/1.0.0/downloads/bbctl-1.0.0-linux-x86-64.tar.gz | tar -xz && mv bbctl /usr/bin/bbctl
# bbctl runtime setup
RUN git clone https://repo1.dso.mil/big-bang/bigbang.git /root/repos/bigbang
# we have cluster admin so just need the file to exist for bbctl - however this tricks the kopf framework so need a different solution
RUN mkdir -p /root/.kube 
#&& touch ~/.kube/config

ENTRYPOINT ["kopf", "run", "/src/operate/handlers.py", "--verbose"]
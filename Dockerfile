FROM python:3.12
COPY . /src
RUN pip install kopf
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && mv kubectl /usr/bin/kubectl
CMD kopf run /src/operate/handlers.py --verbose

FROM python:3.12
COPY . /src
RUN pip install kopf
CMD kopf run /src/operate/handlers.py --verbose

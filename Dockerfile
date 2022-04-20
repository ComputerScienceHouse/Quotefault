FROM python:3.9.8-buster
LABEL maintainer="Joseph Abbate <josephabbateny@gmail.com>"

WORKDIR /app/
RUN apt-get update && apt-get install -y build-essential python3-dev libldap2-dev libsasl2-dev ldap-utils
COPY ./requirements.txt /app/
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./ /app/
COPY ./.git /app/

RUN python -m flask db upgrade; exit 0

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]

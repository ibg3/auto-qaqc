FROM ubuntu:20.04 as base
ENV DEBIAN_FRONTEND=noninteractive \
    NODE_PATH=/usr/src/node-red/.node-red/node_modules:/data/.node-red/node_modules 
USER root
RUN ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime
RUN apt update && apt full-upgrade -y
RUN apt install python3 python3-pip wget screen -y
RUN apt install npm -y
RUN useradd node-red -d /usr/src/node-red && mkdir -p /usr/src/node-red && chown -R node-red /usr/src/node-red
#RUN useradd node-red -d /data && mkdir -p /data && chown -R node-red /data && mkdir -p /usr/src/node-red && chown -R node-red /usr/src/node-red
#USER node-red
#WORKDIR /usr/src/node-red
RUN npm install -g --unsafe-perm node-red
COPY setup.py.diff core.py.diff ./
RUN wget https://files.pythonhosted.org/packages/b8/0e/e7dc632620cca30311f203c957660fcc504d28583d68628b7d1c9edc20aa/pynodered-0.2.0.tar.gz && tar xfvz pynodered-0.2.0.tar.gz && patch pynodered-0.2.0/setup.py setup.py.diff && patch pynodered-0.2.0/pynodered/core.py core.py.diff && tar cfvz pynodered-0.2.0.tar.gz pynodered-0.2.0 && pip3 install pynodered-0.2.0.tar.gz && npm install follow-redirects url querystring && rm -rf pynodered-0.2.0*  && rm ./setup.py.diff
COPY startscript.sh ./
RUN chmod +x ./startscript.sh && chown node-red ./startscript.sh
USER node-red
#RUN mkdir -p ~/.node-red/node_modules && ln -s /usr/src/node-red/node_modules/pynodered ~/.node-red/node_modules/
WORKDIR /data

ENTRYPOINT ["sh", "/startscript.sh"]


FROM jupyter/minimal-notebook

USER root
RUN apt-get update && apt-get install -y s3fs

RUN pip install nuvla-api
RUN pip install docker

ADD nuvla-init.sh /usr/local/bin/nuvla-init.sh
ADD nuvla-integration.py /usr/local/bin/nuvla-integration.py
ADD nuvla-data-mount.py /usr/local/bin/nuvla-data-mount.py

CMD ["/usr/local/bin/nuvla-init.sh"]

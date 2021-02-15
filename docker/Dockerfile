############################################################
# Dockerfile to build PySiQ container images
############################################################

# Set the base image
FROM ubuntu:18.04

# File Author / Maintainer
MAINTAINER Rafael Hernandez <https://github.com/fikipollo>

################## BEGIN INSTALLATION ######################
# INSTALL THE DEPENDENCIES
RUN apt-get update  \
    && apt-get install --no-install-recommends -y apt-transport-https ca-certificates build-essential unzip python3 python3-dev vim uwsgi uwsgi-plugin-python \
    && apt-get clean

COPY configs/* /tmp/

RUN ln -s /usr/bin/python3 /usr/bin/python \
    && python /tmp/get-pip.py \
    && pip install -U pip \
    && pip install -vU pathlib \
    && pip install --upgrade incremental \
    && pip install -r /tmp/requirements.txt

RUN unzip /tmp/pysiq.zip -d /tmp/ \
    && mkdir -p /var/www/pysiq/ \
    && mv /tmp/pysiq/* /var/www/pysiq \
    && rm -r /tmp/pysiq* \
    && mv /tmp/entrypoint.sh /usr/bin/entrypoint.sh \
    && chmod +x /usr/bin/entrypoint.sh \
    && mv /tmp/uwsgi.ini /etc/uwsgi/uwsgi.ini \
    && chown -R www-data:www-data /var/www/pysiq \
    && rm -r /tmp/*

##################### INSTALLATION END #####################

EXPOSE 80

ENTRYPOINT ["/usr/bin/entrypoint.sh"]

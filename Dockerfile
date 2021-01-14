FROM python:3.8
LABEL maintainer="Varis Vecpuisis"

# Install python libs
RUN pip3 install --upgrade pip
COPY ./requirements.txt /opt
RUN cd /opt && pip3 install -r requirements.txt
COPY ./OdooLocust /
RUN pip3 install -e /OdooLocust

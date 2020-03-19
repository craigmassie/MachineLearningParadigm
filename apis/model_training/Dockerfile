FROM jeffreybreen/ubuntu18-blobfuse:0.1
MAINTAINER Craig Massie "2207400m@student.gla.ac.uk"
COPY . /app
WORKDIR /app

RUN apt-get update && \
    apt-get -y install python3.7 python3.7-dev && \
    apt install -y python3-pip && \
    apt install -y dnsutils && \
    python3.7 -m pip install --upgrade pip && \
    pip3 install -r ./requirements.txt && \
    chmod u=rwx mount-blobfuse.sh

ENTRYPOINT ["python3.7"]
CMD ["train_model.py"]
EXPOSE 5000 2222
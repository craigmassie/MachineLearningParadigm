FROM python:3
MAINTAINER Craig Massie "2207400m@student.gla.ac.uk"
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["detect_models.py"]
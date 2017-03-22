FROM ubuntu

RUN apt-get update -y
RUN apt-get install -y git 
RUN apt-get install -y python-pip sqlite3

RUN git clone https://github.com/team-inspix/inspix-server.git
WORKDIR inspix-server
RUN pip install -r requirements.txt 

EXPOSE 5000

CMD ["python", "index.py"]

FROM python

ADD . /opt/chat

WORKDIR /opt/chat
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "main.py"]
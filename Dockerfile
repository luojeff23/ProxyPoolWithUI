FROM python:3.12-slim

WORKDIR /proxy
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0

ADD requirements.txt /proxy
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python", "main.py"]

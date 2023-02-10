# pull official base image
FROM python:3.9-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install library dependencies
# RUN apk add -no-cache --virtual build-dependencies $PACKAGES
RUN apt-get update \
    && apt-get install -y \ 
    build-essential \
    libpq-dev \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# # install dependencies
# RUN pip install --upgrade pip
# RUN pip install numpy pandas

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
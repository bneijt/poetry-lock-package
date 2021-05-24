#Docker container to allow for easy testing with pre-releases of poetry
FROM python

RUN apt-get update && apt-get install -y vim

RUN pip install poetry==1.2.0a1

WORKDIR /test

CMD ["/bin/bash", "/project/in_docker_test.sh"]
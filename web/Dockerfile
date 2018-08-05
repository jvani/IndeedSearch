# -- Start with python image.
FROM python:3.6-slim

# -- Create /app directory and add local dir
WORKDIR /app
ADD . /app

# -- Install gcc.
RUN apt-get update && \
    apt-get -y install gcc git

# -- Install python dependencies.
RUN pip install --trusted-host pypi.python.org -r /app/web/requirements.txt
#RUN pip install git+https://github.com/scrapy/scrapy@master --no-dependencies --upgrade

# -- Run flask app.
CMD ["python", "web/app.py"]


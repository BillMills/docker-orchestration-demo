FROM continuumio/miniconda:latest

# set up conda and apt-get
RUN conda config --set always_yes yes
RUN conda update -q conda
RUN apt-get update

# dependencies
RUN apt-get -y install gcc libpq-dev postgresql
RUN conda install --yes pip
RUN pip install flask psycopg2

# webapp files
RUN mkdir app
ADD app.py /app/.
RUN mkdir /app/templates
ADD templates/index.html /app/templates/.
ADD templates/thanks.html /app/templates/.

# use the postgres user for database communications
USER postgres

# launch the app automatically
CMD sleep 20 && cd app && python app.py
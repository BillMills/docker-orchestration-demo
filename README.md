## docker orchestration demo

This demo illustrates how to use several of Docker's features to launch a simple survey web page, and is suitable for Docker users who have done a basic introduction to starting and stopping containers with `docker run`. Examples will cover basic images and containers, [volumes](https://docs.docker.com/v1.10/engine/userguide/containers/dockervolumes/), and [docker-compose](https://docs.docker.com/compose/).

### a simple web app (in a container)

For this demo, we'll build a simple app: a webpage that asks the visitor to fill out a form, and writes the responses to a postgres database. We'll to use the [official postgres image](https://hub.docker.com/_/postgres/) to provide us with a database service, build our own custom website in a new image, and combine the two via `docker-compose`.

Everything we need for the web part of this demo is found in the `/app` directory. This app is written in python using the [Flask framework](http://flask.pocoo.org/docs/0.11/); it's not necessary to understand the web technology involved to follow the rest of the tutorial, but briefly, `app.py` provides the server-side logic of sending html responses to visitors based on the URLs they provide, as well as handling database interactions; the actual pages that visitors see are described in the html tempaltes in `/app/templates`.

Two other files live in `/app`: `Dockerfile` and `.dockerignore`. `Dockerfile` describes the image that contains the webby part of our app; see this [intro to Dockerfiles](https://docs.docker.com/engine/reference/builder/) if you haven't used them before, and also see [best practices for Dockerfiles](https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/), a few of which are on display here:

 - This container is designed to do exactly one thing: stand up a Flask app that'll interact with a postgres db. There's nothing unnecessary in the `Dockerfile`; just the bare minimum to do this one task.
 - No additional setup is needed after launching a container from this image. The user is set to `postgres`, since this is the default user for a postgres db, and once the container is launched it automatically launches the web app via the final line (after waiting a few seconds to make sure the db is online).

Another best practice mentioned in the link above is the inclusion of a `.dockerignore` file, to make sure nothing unneccessary gets wrapped up in your image. Ours makes sure that preinterpreted python files don't come along for the ride; see [syntax for .dockerignore](https://docs.docker.com/engine/reference/builder/#dockerignore-file) when writing your own.

### docker compose

In the Dockerfile describing our Flask app, we didn't do anything to set up or initialize a database; instead of baking that service into the web app definition, Docker can encapsulate the database in another container, and provide it to the app via [docker compose](https://docs.docker.com/compose/).

Everything Docker needs to know about how to assemble multiple containers into a working app is contained in the `docker-compose.yml`; a complete reference for these files can be found [here](https://docs.docker.com/compose/compose-file/), but below we'll walk through this specific example. 

 - All `docker-compose.yml` files open with `version: '2'`.
 - The `services` key is the most important part of a `docker-compose.yml` file; it lists all the services we want to combine, in our case one called `db` for our database, and one called `app` for our Flask app.
  - `app` contains the following parameters:
    - `build`: build this image from the Dockerfile and assets found in `./app`
    - `links`: indicates what other containers need to be able to communicate with this container via a [Docker network](https://docs.docker.com/engine/userguide/networking/). Note that the string `db` in this case can be used literally within this container in place of a network address; for example, the line `conn = psycopg2.connect("host='db' dbname='postgres' user='postgres'")` uses this to point Python at a postgres database on the host `db`, as if it were communicating with this database over a conventional network.
    - `depends_on`: indicates what other containers are considered dependencies of this one; in this case, `app` won't be launched until `db` is up and running.
    - `ports` maps network ports from `outside`:`inside` the container. In our case, the Flask app is served on port 5000 inside our container, and here we map that onto port 2154 of our docker host (ie the machine we're running Docker on).
  - `db` contains the following parameters:
    - `image`, the counterpart to `build`, indicates the pre-existing image we want to use to stand up this service. In this case, we are using the official postgres image without modifying it in any way.
    - `expose` exposes network ports in this service to the docker network, so other services can connect to it. Postgres communicates by default on 5432, so we make it available with this command.
    - `volumes` mounts data volumes per the mapping `outside`:`inside` the container; in this case, we mount a data volume called `donut-data` that lives on our Docker host on the directory `/var/lib/postgresql/data/donut` inside the `db` container. It's often a good idea to use data volumes with database containers to hold the on-disk record of the database, so that if the database container is destroyed, the data will survive and remain available to re-mount into a new database container. For more details on volumes, see [here](https://docs.docker.com/v1.10/engine/userguide/containers/dockervolumes/).
    - `environment` allows us to set environment variables inside the container. In this case, the `PGDATA` environment variable in the `db` container is set to `/var/lib/postgresql/data/donut` (this makes postgres write its database files to this directory, necessary for those files to end up in the volume mounted above).
 - The `volumes` key allows the declaration of volumes to be mounted within your services; as discussed above, this is commonly used to persist data beyond the lifetime of the container that writes it, or to share data between containers.

If all's gone well, on our docker host in the same directory as `docker-compose.yml`, we can stand up our app via:

```
docker-compose up
```

After about 20 seconds, you should see something like

```
Creating network "dockersurvey_default" with the default driver
Creating dockersurvey_db_1
Creating dockersurvey_app_1
Attaching to dockersurvey_db_1, dockersurvey_app_1
db_1   | LOG:  database system was shut down at 2016-10-05 17:23:51 UTC
db_1   | LOG:  MultiXact member wraparound protections are now enabled
db_1   | LOG:  autovacuum launcher started
db_1   | LOG:  database system is ready to accept connections
app_1  |  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

indicating that your app is running. The first time we stand up our app, `docker-compose` will build the `app` image; if we ever change that Dockerfile or dependencies in future, the build must be explicitly repeated by first running `docker-compose build`. Have a look at what containers `docker-compose` has produced by doing `docker ps` on your host machine:

```
Bills-MBP:docker-survey billmills$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
2260eab7d065        dockersurvey_app    "/usr/bin/tini -- /bi"   5 seconds ago       Up 3 seconds        0.0.0.0:2154->5000/tcp   dockersurvey_app_1
f58dad507009        postgres            "/docker-entrypoint.s"   6 seconds ago       Up 4 seconds        5432/tcp                 dockersurvey_db_1
```

One for each service listed in our compose file. Visit your survey in your browser at `127.0.0.1:2154`, fill out the form, and submit, then back on your docker host in a new shell tab, connect to your postgres database directly (use the `CONTAINER ID` listed with your own `postgres` image in the output from `docker ps`):

```
docker exec -it f58dad507009  /bin/bash
```

this logs us into the `postgres` container, from where we can explore the database:

```
root@f58dad507009:/# psql --username=postgres                                                                                                                                                              
psql (9.6.0)
Type "help" for help.

postgres=# select * from cats;
 name |  coat  |   donut  
------+--------+------------
 Pika | tortie | strawberry

(3 rows)

postgres=# 
```

Which should correspond to what we entered in the app. Do a `\q` to exit the `psql` prompt, then back on your docker host, `ctrl-c` to kill the running app, and clean up with:

```
docker-compose down
```

Restart everything from the `docker-compose up` command and connect to your `postgres` container again exactly as above, and you should see the same stuff listed in your database; the volume has persisted the database files between app shutdown, cleanup and restart.

### conclusion

In the above, we made a simple web app architected with Docker to separate services in isolated containers, and connect them together with Docker Compose. The beauty of this approach is the *standardization* it allows; we didn't have to do any postgres setup *at all* - the postgres folks set up postgres as a service in the official `postgres` image, and we were able to plug our web app into it without any modification. In this way, Docker allows us to think about service provisioning more like interacting with an external API, as opposed to the creation of monolith stacks with all services coexisting on the same machine.

Docker Compose can do much more beyond this, too. In [this tutorial](http://success.docker.com/Datacenter/Apply/Reference_Architecture%3A_Service_Discovery_and_Load-Balancing_with_Docker_Universal_Control_Plane_(UCP)), you'll see how Compose can scale up the number of containers available to provide a service, and abstract away the assignment of compute tasks to those workers so that your app can seamlessly scale from using a single container during prototyping, to a whole datacenter's worth in production with no re-engineering at all.

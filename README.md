# Jupyter Notebook

An example [Jupyter Notebook](https://jupyter.org/) that integrates
well with [Nuvla](https://docs.nuvla.io/).

## Supported tags and respective `Dockerfile` links

Multi-architecture tags: 

 - `latest` ([Dockerfile](https://github.com/nuvla/example-jupyter/blob/master/Dockerfile))

Architecture-specific tags:

 - `latest-amd64` ([Dockerfile](https://github.com/nuvla/example-jupyter/blob/master/Dockerfile))

## How to use this image

To run the container:

```sh
docker run -d -p :8888 nuvla/jupyter
```

You can then access the container using a URL of the form:

```
https://host:port/?token=...
```

where the host is given by the Swarm cluster, port is the mapping for
port 8888, and token is the value written to the container log (and as
a Nuvla output parameter). The container uses a self-signed
certificate.

Use the standard Docker commands to stop and remove the container.

## How to build this image

To build the container on your current platform, clone the sources
from the
[nuvla/example-jupyter](https://github.com/nuvla/example-jupyter)
GitHub, then run the following Docker command:

```sh
docker build . --tag nuvla/example-jupyter
```

To build the container for all supported platforms, run the commands:

```sh
./.travis.before_install.sh
./.travis.script.sh
```

The `before_install.sh` script may not be necessary if "binfmt_misc"
support is already included in your Docker installation (e.g. MacOS).

# Jupyter Notebook

An example [Jupyter Notebook](https://jupyter.org/) that integrates
well with [Nuvla](https://docs.nuvla.io/).

## How to register this image in a Nuvla installation

To register this container on your Nuvla on-premise installation, clone the
sources from the
[nuvla/example-jupyter-data](https://github.com/nuvla/example-jupyter) GitHub,
change directory into `s3-mount`, then run the following commands, after having
exported the required environment variables:

```sh
pip install nuvla-api
python add-module.py
```

You should now see the module component in the App Store called *Jupyter Notebook*.

## How to use image from Nuvla

This image is intended to be launched from Nuvla with data provided to the
deployment via "Open With..." feature of Nuvla. This requires a pre-defined data
set with a filter over the data records registered in Nuvla as `data-record`
data types.

## How to use this image locally

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

To build the container on your current platform, clone the sources from the
[nuvla/example-jupyter-data](https://github.com/nuvla/example-jupyter) GitHub,
change directory to `s3-mount` sub-folder and then run the following Docker
command:

```sh
docker build . --tag nuvla/example-jupyter-data:$(cat version.txt)
```


GIT_COMMIT = $(shell git rev-parse --short HEAD)
REGISTRY_ADDRESS = vi-nexus.lab.vi.local
CONTAINER_NAME = docker-openstack-swift
TAG = $(GIT_COMMIT)
DEFAULT_GOAL := build

start: build run

run:
	docker run -it --rm --name=$(CONTAINER_NAME) -p 8080:8080 $(REGISTRY_ADDRESS)/$(CONTAINER_NAME)

build:
	docker build --tag=$(REGISTRY_ADDRESS)/$(CONTAINER_NAME):$(TAG) --tag=$(REGISTRY_ADDRESS)/$(CONTAINER_NAME):latest .

shell:
	docker exec -it $(CONTAINER_NAME) bash

push:
	docker push $(REGISTRY_ADDRESS)/$(CONTAINER_NAME):$(TAG)
	docker push $(REGISTRY_ADDRESS)/$(CONTAINER_NAME):latest

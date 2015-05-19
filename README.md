HTCondor Galaxy Docker Image
============================

This repository acts as a layer on top of the [Galaxy Docker](https://github.com/bgruening/docker-galaxy-stable) image, providing support for using [HTCondor](http://research.cs.wisc.edu/htcondor/) on a remote server as a scheduler for [Galaxy](http://galaxyproject.org/). For general setup of the underlying Galaxy Docker image, [see its page](https://github.com/bgruening/docker-galaxy-stable).

Usage
=====

After installing the image, you can run it with

    docker run -d -p 80:80 -p 21:21 dpryan79/htcondor-galaxy

As with the underlying Galaxy Docker image, users are advised to mount a writeable directory to `/export`:

    docker run -d -p 80:80 -p 21:21 -v /data/galaxy:/export dpryan79/htcondor-galaxy

This will result in the container writing configuration and database files to `/data/galaxy`, thereby allowing saving of state and users. In particurlar, if `/export/condor_config` exists, it will be used as the configuration file when starting the HTCondor services from within the container. This is convenient, since it allows you to modify and save the the settings for HTCondor for subsequent use.

Configuring Galaxy To Use HTCondor
==================================

To be written

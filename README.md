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

Configuring HTCondor
====================

HTCondor must be properly configured both with and outside docker for jobs to actually run. The easiest way to troubleshoot this is as the galaxy user from within the docker container (i.e., not as root, but also not through the Galaxy interface, we'll get to that next).

The simplest method is to use host-based authentication for everything. The docker container will typically receive an IP address in the 172.17.*.* range, so use that in the various condor_config files.

Assuming you want to use the base linux machine as the controller/runner of jobs and the Galaxy instance within docker only to submit jobs, then the `condor_config` file exported to Galaxy (i.e., `/export/condor_config`), should contain the following settings:

    CONDOR_HOST = whatever.your.host.ip.is
    FLOCK_TO = 172.17.42.1
    ALLOW_READ = 172.17.*
    ALLOW_WRITE = 172.17.*
    ALLOW_NEGOTIATE = 172.17.*
    DAEMON_LIST = MASTER, SCHEDD

The `CONDOR_HOST` field should be whatever the IP address of the base Linux installation is. Similarly, the `FLOCK_TO` address should be that given to the docker interface (see `ifconfig docker0`). The `DAEMON_LIST` entry doesn't strictly need to be customized, though it prevents extraneous daemons from starting.

On the host server, the `condor_config` settings should be similar:

    ALLOW_READ = $(IP_ADDRESS), 172.17.*
    ALLOW_WRITE = $(IP_ADDRESS), 172.17.*
    ALLOW_NEGOTIATOR = $(IP_ADDRESS), 172.17.*
    FLOCK_FROM = $(IP_ADDRESS), 172.17.*

Warnings
--------

A few warnings are in order. Firstly, changing/restarting HTCondor within docker or on the host will typically lead to a long delay before jobs can be properly submitted. If you restart both then job submission will tend to procede in a more timely manner.

Logs are found under `/var/log/condor`. If you run into "PERMISSION DENIED" messages, try changing the verious `ALLOW_*` lines to be equal to simply `*`. Note that it's most convenient to restart the HTCondor services both on the base Linux server and within the Docker instance. Within the instance, a simple `/etc/init.d/condor restart` will suffice (the method used on the base Linux instance will vary).

For the purposes of debugging, a simple script for `condor_submit` would be:

    executable = /bin/mount
    universe = vanilla
    output = test.out
    log = test.log
    queue

Saving that as "test.txt" and then running `condor_submit test.txt` will queue the job. The output will be printed to `test.out` and a log to `test.log`. Note that this should be run as the galaxy user (i.e., `su galaxy` first). Similar test scripts can be made with `sleep` and `hostname`.

In the off chance that errors occur while starting this Docker image (e.g., "Error response from daemon, Cannot start container ... too many levels of symbolic links"), just try again and this will work (this seems to be due to remnant soft-links).

Configuring Galaxy To Use HTCondor
==================================

To be written

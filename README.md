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
    UID_DOMAIN = BioInfoCluster
    DAEMON_LIST = MASTER, SCHEDD

The `CONDOR_HOST` field should be whatever the IP address of the base Linux installation is. Similarly, the `FLOCK_TO` address should be that given to the docker interface (see `ifconfig docker0`). The `DAEMON_LIST` entry doesn't strictly need to be customized, though it prevents extraneous daemons from starting. Note that the `UID_DOMAIN` can be anything you want but needs to be the same both within and outside of Docker.

On the host server, the `condor_config` settings should be similar:

    ALLOW_READ = $(IP_ADDRESS), 172.17.*
    ALLOW_WRITE = $(IP_ADDRESS), 172.17.*
    ALLOW_NEGOTIATOR = $(IP_ADDRESS), 172.17.*
    FLOCK_FROM = $(IP_ADDRESS), 172.17.*
    UID_DOMAIN = BioInfoCluster
    SOFT_UID_DOMAIN = TRUE
    TRUST_UID_DOMAIN = TRUE

In addition, a user named `galaxy` on the linux runner nodes is needed. The uid needs to be 1450 to match that in the docker container. The reason for this is that otherwise it's difficult to get HTCondor to run jobs in a way such that they can write their output in a directory accessible to docker. The various `UID_DOMAIN` related parameters setup both the "run as the galaxy user" part and the filesystem permissions part. You will also need to create two sym-links:

    ln -s /export /data/galaxy #Or whereever you're binding /export from within Docker
    ln -s /galaxy-central /data/galaxy/galaxy-central

The above two symbolic links need to be present on each runner node and need to point to an appropriate shared mount point. This allows partially for a shared filesystem between the runner nodes and Docker.

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

You will need at least the following in `config/job_conf.xml`:

    <?xml version="1.0"?>
    <job_conf>
        <plugins workers="2">
            <plugin id="local" type="runner" load="galaxy.jobs.runners.local:LocalJobRunner"/>
            <plugin id="condor" type="runner" load="galaxy.jobs.runners.condor:CondorJobRunner"/>
        </plugins>
        <handlers default="handlers">
            <handler id="handler0" tags="handlers"/>
            <handler id="handler1" tags="handlers"/>
        </handlers>
        <destinations default="local">
            <destination id="local" runner="local"/>
            <destination id="condor" runner="condor"/>
        </destinations>
        <tools>
            <tool id="toolshed.g2.bx.psu.edu/repos/devteam/bowtie2/bowtie2/0.4" destination="condor"/>
        </tools>
    </job_conf>

The entry under "tools" for bowtie2 is just an example. Note that by default everything is run *within* the Docker container. The reason for this is that things like uploading files use python programs that require modules specific to Galaxy. Unless you happen to have Galaxy installed on each of your runner nodes, none of these python scripts will work. Consequently, it's simplest to specify tools that you instead want to run remotely. Things from the toolshed (e.g., bedtools, bowtie2, bwa, etc.) will typically work. You then need to add an entry for each of these under the "tools" section.

Unresolved issues
-----------------

There is currently one unresolved problem. After jobs are run on a runner node, the jobs attempts to update its metadata. This uses a python script that attempts to import a Galaxy-specific module. Since this step runs outside of docker it fails. Consequently you'll typically see the following in stderr for each job run remotely:

    Traceback (most recent call last):
    File "/export/galaxy-central/database/job_working_directory/000/132/set_metadata_M9CksR.py", line 1, in <module>
        from galaxy_ext.metadata.set_metadata import set_metadata; set_metadata()
    ImportError: No module named galaxy_ext.metadata.set_metadata

Some of the specifics will be different for each job. The job will still complete and the results will still be handled seemingly properly by Galaxy. An issue in [the Galaxy Trello board](https://trello.com/c/KnvdRRlj) has been made for this bug. It's currently unclear how big of a problem this is.

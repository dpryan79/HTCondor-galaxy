#!/usr/bin/env python
import subprocess
import os

def condor_configExists() :
    if(os.access("/export/condor_config", os.F_OK)) :
        return True
    return False

def lnConfig() :
    os.remove("/etc/condor/condor_config")
    os.symlink("/export/condor_config","/etc/condor/condor_config")

def main() :
    if(condor_configExists()) :
        try :
            lnConfig()
        except :
            sys.stderr.write("Couldn't link to /export/condor_config, using the default configuration\n")
    #Start the condor service
    cmd = ["bash", "/etc/init.d/condor", "start"]
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()

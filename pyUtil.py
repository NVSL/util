import subprocess

def docmd(cmd, simulate=False):
    if simulate:
        print cmd
    else:
        print cmd
        subprocess.call(cmd, shell=True)       

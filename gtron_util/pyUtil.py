import subprocess

def docmd(cmd, simulate=False):
    if simulate:
        print cmd
    else:
        subprocess.call(cmd, shell=True)       

import subprocess

def docmd(cmd, simulate=False, stderr=None, stdout=None, stdin=None):
    if simulate:
        print cmd
    else:
        subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr, stdin=stdin)

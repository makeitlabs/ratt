import os
import tarfile
from fabric import task

@task
def uname(conn):
    result = conn.run('uname -a', hide=True)
    msg = "Ran {0.command!r} on {0.connection.host} and got stdout:\n{0.stdout}"
    print(msg.format(result))

@task
def devup(conn):
    os.chdir(os.path.expanduser("~/ratt/firmware/rpi/app"))

    tar = tarfile.open("/tmp/app-update.tar.gz", "w:gz");
    for name in ["."]:
        tar.add(name)

    tar.close()

    conn.put("/tmp/app-update.tar.gz", "/tmp")

    conn.run("rm -rf /tmp/ratt") 
    conn.run("mkdir /tmp/ratt")

    conn.run("tar xvzf /tmp/app-update.tar.gz -C /tmp/ratt")


@task
def deploy(conn):
    os.chdir(os.path.expanduser("~/ratt/firmware/rpi/app"))

    tar = tarfile.open("/tmp/app-update.tar.gz", "w:gz");
    for name in ["."]:
        tar.add(name)

    tar.close()

    conn.put("/tmp/app-update.tar.gz", "/tmp")

    conn.run("systemctl stop ratt-app")

    conn.run("rm -rf /usr/ratt.old") 
    conn.run("mv /usr/ratt /usr/ratt.old")
    conn.run("mkdir /usr/ratt")

    conn.run("tar xvzf /tmp/app-update.tar.gz -C /usr/ratt")

    conn.run("systemctl start ratt-app")

@task
def revert(conn):
    conn.run("systemctl stop ratt-app")

    conn.run("rm -rf /usr/ratt") 
    conn.run("mv /usr/ratt.old /usr/ratt")

    conn.run("systemctl start ratt-app")

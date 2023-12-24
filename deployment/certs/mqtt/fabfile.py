import os
from fabric import task, config

@task
def deploy_certs(conn, cn=None):

    print("deploy_certs cn=" + cn)
    if cn:
        conn.run("mkdir -p /data/certs")
        print("Copying CA certificate...")
        conn.put("ssl/certs/ca.crt", "/data/certs/ca.crt")
        print("Copying client certificate...")
        conn.put("ssl/certs/client_" + cn + ".crt", "/data/certs/client.crt")
        print("Copying client private key...")
        conn.put("ssl/private/client_" + cn + ".key", "/data/certs/client.key")
        print("CA cert:")
        conn.run("openssl x509 -in /data/certs/ca.crt -subject -noout")
        print("Client cert:")
        conn.run("openssl x509 -in /data/certs/client.crt -subject -noout")
        print("Client private key:")
        conn.run("openssl rsa -in /data/certs/client.key -noout -check")

@task
def deploy_doorbot_certs(conn, cn=None):

    print("deploy_doorbot_certs cn=" + cn)
    if cn:
        conn.run("mkdir -p /home/pi/ssl")
        print("Copying CA certificate...")
        conn.put("ssl/certs/ca.crt", "/home/pi/ssl/ca.crt")
        print("Copying client certificate...")
        conn.put("ssl/certs/client_" + cn + ".crt", "/home/pi/ssl")
        print("Copying client private key...")
        conn.put("ssl/private/client_" + cn + ".key", "/home/pi/ssl")
        print("CA cert:")
        conn.run("openssl x509 -in /home/pi/ssl/ca.crt -subject -noout")
        print("Client cert:")
        conn.run("openssl x509 -in /home/pi/ssl/client.crt -subject -noout")
        print("Client private key:")
        conn.run("openssl rsa -in /home/pi/ssl/client.key -noout -check")

@task
def restart_app(conn):
    print("Restarting app...")
    conn.run("systemctl stop ratt-app")
    conn.run("systemctl start ratt-app")

@task
def test(conn):
    print("Testing... you should see the output from uname -a");
    conn.run("uname -a")

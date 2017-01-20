# sample apache configs

These config skeletons demonstrate how to configure apache sites for use with the self-signed certs configured in the 'certs' directory in the root of this example.

'authbackend-ssl.conf' is for a Flask/WSGI instance of the MakeIt Labs authbackend, and runs two instances of the backend: one on regular https (443) which does not require client certs, and one on port 8443 which does.

'basic-site-ssl.conf' is a simpler example which serves plain old static content out of /var/www/html over https (443).

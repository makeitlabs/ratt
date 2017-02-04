# Self-signed certificates

A simple script called 'gencerts.sh' generates a CA, and self-signed server and client certificates in various formats.  These certs are copied down into the build directory for the ESP example, as the CA cert, client cert, and client private key are baked into the firmware.

Another script called 'curl-authbackend-api-test.sh' is a sample curl command line to test against a secure server configured with the MakeIt Labs authbackend and the certs configured above.

See the 'apache' directory in the root of this example for sample apache configs that use the certs generated within.

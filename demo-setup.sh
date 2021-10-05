# Setup and install local cloud with mandatory + eventhandler in insecure mode
pyrrowhead cloud setup demo.lubeck -d . --ssl-disabled --include eventhandler --install
pyrrowhead cloud up demo.lubeck -d .

# Build arguments for version control
ARG POSTGRES_VERSION=17
ARG ALPINE_VERSION=3.22

FROM postgres:${POSTGRES_VERSION}-alpine${ALPINE_VERSION}

# Copy the initialization script to the docker-entrypoint-initdb.d directory
COPY init-db.sql /docker-entrypoint-initdb.d/

# Set proper permissions
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sql

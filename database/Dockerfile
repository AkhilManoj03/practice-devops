FROM postgres:17-alpine3.21

# Copy the initialization script to the docker-entrypoint-initdb.d directory
COPY init-db.sql /docker-entrypoint-initdb.d/

# Set proper permissions
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sql

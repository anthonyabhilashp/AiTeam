# Database Initialization with Flyway
FROM flyway/flyway:9.22-alpine

# Copy migration files
COPY sql/ /flyway/sql/

# Set Flyway configuration via environment variables
ENV FLYWAY_BASELINE_ON_MIGRATE=true
ENV FLYWAY_VALIDATE_ON_MIGRATE=true
ENV FLYWAY_OUT_OF_ORDER=true

# Default command
CMD ["migrate"]

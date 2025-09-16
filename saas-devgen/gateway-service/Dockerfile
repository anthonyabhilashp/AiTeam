# Gateway Service Dockerfile using Kong
FROM kong:3.7

# Copy Kong configuration files
COPY kong.conf /etc/kong/kong.conf
COPY kong.yml /usr/local/kong/kong.yml

# Create SSL directory
RUN mkdir -p /usr/local/kong/ssl

# Create logs directory
RUN mkdir -p /usr/local/kong/logs

# Set proper permissions
RUN chmod 644 /etc/kong/kong.conf /usr/local/kong/kong.yml

# Expose ports
EXPOSE 8000 8443 8001 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8001/status || exit 1

# Start Kong
CMD ["kong", "start", "-c", "/etc/kong/kong.conf"]

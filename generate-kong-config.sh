#!/bin/bash

# Generate Kong configuration with environment variables
AUTH_PORT=${AUTH_SERVICE_PORT:-8004}

cat > saas-devgen/gateway-service/kong.yml << EOF
_format_version: "3.0"

services:
  - name: auth-service
    url: http://auth-service:${AUTH_PORT}
    routes:
      - name: auth-route
        paths:
          - /auth
        methods:
          - GET
          - POST
          - PUT
          - DELETE
        strip_path: false

plugins:
  - name: cors
    config:
      origins:
        - http://localhost:3000
        - https://localhost:3000
      methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Accept-Version
        - Content-Length
        - Content-MD5
        - Content-Type
        - Date
        - X-Auth-Token
        - Authorization
      exposed_headers:
        - X-Auth-Token
      credentials: true
      max_age: 3600

  - name: request-transformer
    config:
      add:
        headers:
          - "X-Forwarded-Proto: https"
      remove:
        headers:
          - "X-Forwarded-For"

consumers:
  - username: admin-user
    custom_id: admin-001

  - username: api-user
    custom_id: api-001

upstreams:
  - name: auth-upstream
    targets:
      - target: auth-service:${AUTH_PORT}
        weight: 100
EOF

echo "Kong configuration generated with AUTH_SERVICE_PORT=${AUTH_PORT}"

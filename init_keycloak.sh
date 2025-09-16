#!/bin/bash
# Keycloak Initialization Script

echo "🔧 Initializing Keycloak..."

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
until curl -f http://localhost:8080/realms/master/.well-known/openid-connect-configuration > /dev/null 2>&1; do
    echo "Waiting for Keycloak..."
    sleep 5
done

echo "✅ Keycloak is ready!"

# Get admin token
echo "🔑 Getting admin token..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token"
    exit 1
fi

echo "✅ Got admin token"

# Create realm
echo "🏰 Creating realm 'devgen'..."
curl -s -X POST http://localhost:8080/admin/realms \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "devgen",
    "enabled": true,
    "displayName": "DevGen Platform"
  }'

# Create client
echo "📱 Creating client 'auth-service'..."
curl -s -X POST http://localhost:8080/admin/realms/devgen/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "auth-service",
    "enabled": true,
    "protocol": "openid-connect",
    "publicClient": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": true,
    "implicitFlowEnabled": false,
    "standardFlowEnabled": true,
    "secret": "client-secret"
  }'

# Get client ID
echo "🔍 Getting client ID..."
CLIENT_ID=$(curl -s http://localhost:8080/admin/realms/devgen/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.[] | select(.clientId=="auth-service") | .id')

if [ -z "$CLIENT_ID" ]; then
    echo "❌ Failed to get client ID"
    exit 1
fi

echo "✅ Client ID: $CLIENT_ID"

# Create admin role
echo "👑 Creating admin role..."
curl -s -X POST http://localhost:8080/admin/realms/devgen/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "admin",
    "description": "Administrator role"
  }'

# Create user role
echo "👤 Creating user role..."
curl -s -X POST http://localhost:8080/admin/realms/devgen/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user",
    "description": "Regular user role"
  }'

# Create admin user
echo "👨‍💼 Creating admin user..."
curl -s -X POST http://localhost:8080/admin/realms/devgen/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "firstName": "Admin",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "admin",
      "temporary": false
    }]
  }'

# Get user ID
echo "🔍 Getting user ID..."
USER_ID=$(curl -s http://localhost:8080/admin/realms/devgen/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.[] | select(.username=="admin") | .id')

if [ -z "$USER_ID" ]; then
    echo "❌ Failed to get user ID"
    exit 1
fi

echo "✅ User ID: $USER_ID"

# Assign admin role to user
echo "🔗 Assigning admin role to user..."
curl -s -X POST http://localhost:8080/admin/realms/devgen/users/$USER_ID/role-mappings/realm \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name": "admin"}]'

echo "🎉 Keycloak initialization completed successfully!"
echo ""
echo "📋 Summary:"
echo "  Realm: devgen"
echo "  Client: auth-service (secret: client-secret)"
echo "  Admin User: admin / admin"
echo "  Roles: admin, user"

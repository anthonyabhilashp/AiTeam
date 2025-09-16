FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY saas-devgen/frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy the rest of the application
COPY saas-devgen/frontend/ .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["npm", "start"]

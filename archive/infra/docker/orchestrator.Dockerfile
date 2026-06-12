FROM node:20-alpine

WORKDIR /app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy schema package first (dependency)
COPY packages/schema/ ./packages/schema/

# Build schema package
WORKDIR /app/packages/schema
RUN npm install && npm run build

# Copy orchestrator package files
WORKDIR /app/orchestrator
COPY apps/orchestrator/package*.json ./

# Install dependencies (includes local schema package)
RUN npm install

# Copy orchestrator source
COPY apps/orchestrator/ ./

# Build TypeScript
RUN npm run build

WORKDIR /app/orchestrator

EXPOSE 3000

CMD ["npm", "start"]

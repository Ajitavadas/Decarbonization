# Development Dockerfile for Next.js
FROM node:20-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache libc6-compat curl

# Copy package files
COPY package.json ./
RUN npm install

# Copy application code
COPY . .

EXPOSE 3000

ENV NEXT_TELEMETRY_DISABLED 1
ENV PORT 3000

CMD ["npm", "run", "dev"]


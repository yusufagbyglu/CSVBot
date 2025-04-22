# Frontend Dockerfile
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project files
COPY . .

# Build the app
RUN npm run build

# Expose port (Vite default is 5173)
EXPOSE 5173

# Start the app
CMD ["npm", "run", "preview", "--", "--host"]

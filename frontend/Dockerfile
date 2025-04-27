FROM node:18-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git
COPY package.json package-lock.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Command to run the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 
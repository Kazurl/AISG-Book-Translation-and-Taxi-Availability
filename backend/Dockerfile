# Use official Node.js image as the base image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Copy dependencies files and install them
COPY package*.json ./
RUN npm install

# Copy all source files
COPY . .

ENV NODE_ENV=production

# Expose the port the app runs on
EXPOSE 5001

# Run app
CMD ["npm", "run", "start"]
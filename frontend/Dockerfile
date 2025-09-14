FROM node:20-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve with nginx for production
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
FROM node:20-alpine
WORKDIR /app

# Enable Next.js telemetry if you want or leave it disabled
ENV NEXT_TELEMETRY_DISABLED 1

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]

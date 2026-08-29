FROM node:22.13-slim
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_PUBLIC_SITE_URL=http://localhost:3000
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0"]

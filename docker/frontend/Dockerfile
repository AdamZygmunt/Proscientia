# Dev image for Vite + React + TS + Tailwind (HMR inside Docker)
FROM node:20-alpine AS dev

# Ustawienia środowiska dev + lepszy hot-reload na Windows/WSL/Docker Desktop
ENV NODE_ENV=development \
    HOST=0.0.0.0 \
    CHOKIDAR_USEPOLLING=true

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

EXPOSE 5173

# Uruchomienie dev serwera:
# -- host 0.0.0.0 potrzebne, aby był widoczny z hosta/compose
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

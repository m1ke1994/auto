FROM node:22-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm ci

FROM deps AS dev

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

FROM deps AS build

ARG VITE_API_URL=https://tracknode.ru/api
ARG VITE_BACKEND_URL=https://tracknode.ru
ARG VITE_SITE_SLUG=novaya-konakova
ARG VITE_SITE_URL=https://novoe-konakovo.ru
ARG VITE_PUBLIC_SITE_URL=https://novoe-konakovo.ru

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_SITE_SLUG=$VITE_SITE_SLUG
ENV VITE_SITE_URL=$VITE_SITE_URL
ENV VITE_PUBLIC_SITE_URL=$VITE_PUBLIC_SITE_URL

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

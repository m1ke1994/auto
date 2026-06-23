FROM node:22-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm ci \
    && npm install --no-save @rollup/rollup-linux-x64-musl

FROM deps AS dev

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

FROM deps AS build

ARG VITE_API_URL
ARG VITE_BACKEND_URL
ARG VITE_SITE_SLUG=a-meditation
ARG VITE_SITE_URL
ARG VITE_PUBLIC_SITE_URL

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_SITE_SLUG=$VITE_SITE_SLUG
ENV VITE_SITE_URL=$VITE_SITE_URL
ENV VITE_PUBLIC_SITE_URL=$VITE_PUBLIC_SITE_URL

COPY . .
RUN test -n "$VITE_API_URL" && test -n "$VITE_BACKEND_URL" && test -n "$VITE_SITE_URL" && test -n "$VITE_PUBLIC_SITE_URL"
RUN npm run build

FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

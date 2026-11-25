FROM node:22-alpine
WORKDIR /opt/studio
RUN npm install --no-audit --no-fund --ignore-scripts vue@3.5.34 vite@6.4.1 @vitejs/plugin-vue@5.2.4 three@0.180.0 gsap@3.13.0 lenis@1.3.20
# Vite uses preinstalled platform binaries. Build source is copied at runtime.
RUN mkdir /work && chown node:node /work
USER node
WORKDIR /work
ENTRYPOINT ["sh","-c","cp -R /source/. /work/ && ln -s /opt/studio/node_modules /work/node_modules && /opt/studio/node_modules/.bin/vite build --outDir /work/dist && cp -R /work/dist/. /output/"]

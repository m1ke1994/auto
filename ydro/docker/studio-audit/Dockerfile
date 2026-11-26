FROM mcr.microsoft.com/playwright:v1.64.1-noble
WORKDIR /opt/audit
RUN npm install --no-audit --no-fund --ignore-scripts playwright@1.64.1
COPY audit.mjs asset-preview.mjs capture.mjs capture.test.mjs hero-smoke.mjs studio-flow.mjs cinematic-studio-flow.mjs queue-cinematic.mjs inspect-cinematic.mjs ./
RUN node --check audit.mjs && node --check hero-smoke.mjs && node --check studio-flow.mjs && node --check cinematic-studio-flow.mjs && node --check queue-cinematic.mjs && node --check inspect-cinematic.mjs && node --test capture.test.mjs
USER pwuser
ENV HOME=/tmp
ENTRYPOINT ["node","/opt/audit/audit.mjs"]

FROM mcr.microsoft.com/playwright:v1.64.1-noble
WORKDIR /opt/audit
RUN npm install --no-audit --no-fund --ignore-scripts playwright@1.64.1
COPY audit.mjs asset-preview.mjs capture.mjs capture.test.mjs ./
RUN node --check audit.mjs && node --test capture.test.mjs
USER pwuser
ENV HOME=/tmp
ENTRYPOINT ["node","/opt/audit/audit.mjs"]

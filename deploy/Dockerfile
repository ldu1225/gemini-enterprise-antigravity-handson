# Non-root nginx (uid 101, listens on 8080) — exact patch version pinned.
FROM nginxinc/nginx-unprivileged:1.28.0-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security_headers.conf /etc/nginx/snippets/security_headers.conf
COPY site/ /usr/share/nginx/html/

EXPOSE 8080

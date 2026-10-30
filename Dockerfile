FROM nginx:alpine

# Copy the static site
COPY website/site /usr/share/nginx/html

# Replace the default nginx config with ours
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Validate config at build time: a syntax error fails the build, not the site.
RUN nginx -t

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

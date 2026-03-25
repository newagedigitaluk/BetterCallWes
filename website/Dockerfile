FROM nginx:alpine

# Copy the static site
COPY site/Website /usr/share/nginx/html

# Replace the default nginx config with ours
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

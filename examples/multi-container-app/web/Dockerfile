FROM nginx:1.30-alpine
# Which container the /api/ requests go to (change with -e API_HOST=...)
ENV API_HOST=api
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY html/ /usr/share/nginx/html/
EXPOSE 80

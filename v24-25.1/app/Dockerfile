FROM alpine
RUN apk add busybox-extras curl
COPY index.cgi var/www/cgi-bin/
EXPOSE 81
CMD httpd -p 81 -h /var/www -f -vv

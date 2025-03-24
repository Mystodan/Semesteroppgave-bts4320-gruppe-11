FROM alpine
RUN apk add busybox-extras libxml2-utils sqlite mkpasswd
COPY index.cgi var/www/cgi-bin/

# Lager en katalog hvor bidrag databasen monteres.
RUN mkdir -p /var/www/bidrag

# Endre på tilatelser til katalogen til bidrag databasen.
RUN chmod a+w /var/www
RUN chmod a+w /var/www/bidrag

EXPOSE 82
CMD httpd -p 82 -h /var/www -f -vv

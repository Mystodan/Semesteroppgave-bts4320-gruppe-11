FROM alpine
RUN apk add busybox-extras libxml2-utils sqlite
COPY index.cgi var/www/cgi-bin/

# Lager en katalog hvor pseudonym databasen monteres.
RUN mkdir -p /var/www/pseudonym

# Endre på tilatelser til katalogen til pseudonym databasen.
RUN chmod a+w /var/www
RUN chmod a+w /var/www/pseudonym

EXPOSE 83
CMD httpd -p 83 -h /var/www -f -vv

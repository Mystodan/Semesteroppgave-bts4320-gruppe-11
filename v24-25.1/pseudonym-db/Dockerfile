FROM alpine
RUN apk add busybox-extras libxml2-utils sqlite
COPY index.cgi var/www/cgi-bin/

RUN echo "CREATE TABLE Pseudonym (           \
  epost         VARCHAR(200) PRIMARY KEY, \
  pseudonym     VARCHAR(200),             \
  salt          VARCHAR(11),              \	
  passordhash   VARCHAR(44))" | sqlite3 var/www/pseudonym.db

# for I in Ante Bjart Cecilie; do echo "$I@example.com" | pwgen  8 1 -0 -A -H /dev/stdin;done
# for I in 123 234 345; do mkpasswd -m sha-256 -S $(date +%s) $I;sleep 1;done

RUN echo "INSERT INTO Pseudonym (epost, pseudonym, salt, passordhash) VALUES                \
   ('Ante@example.com'   ,'osiedahs', '1712167670', 'Aw16YyLRWTS0BOoOb7DpvBMeYb444g.kl1a542GYpJA' ), \
   ('Bjart@example.com'  ,'uozaixav', '1712167671', 'q37QpOdM2jSDeXOVAyiCSzMgy08dI7pLQ1aBElJps48' ), \
   ('Cecilie@example.com','olaebaev', '1712167672', 'D0z6dLRTSw.u7tct9zQVBUOCBhPEiFn2Eb./li.oyUA' )" \
   | sqlite3 var/www/pseudonym.db

RUN chmod a+w var/www/pseudonym.db
EXPOSE 83
CMD httpd -p 83 -h /var/www -f -vv

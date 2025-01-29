FROM alpine
RUN apk add busybox-extras libxml2-utils sqlite mkpasswd
COPY index.cgi var/www/cgi-bin/

RUN echo "CREATE TABLE Bidrag (              \
  pseudonym        VARCHAR(200) PRIMARY KEY, \
  salt             VARCHAR(11),              \	
  passordhash      VARCHAR(44),              \
  kommentar        VARCHAR(1000),            \
  offentlig_nokkel VARCHAR(200),             \
  tittel           VARCHAR(100),             \
  tekst            VARCHAR(1000))" | sqlite3 var/www/bidrag.db

RUN echo "INSERT INTO Bidrag (pseudonym, salt, passordhash) VALUES             \
   ('osiedahs', '1712167670', 'Aw16YyLRWTS0BOoOb7DpvBMeYb444g.kl1a542GYpJA' ), \
   ('uozaixav', '1712167671', 'q37QpOdM2jSDeXOVAyiCSzMgy08dI7pLQ1aBElJps48' ), \
   ('olaebaev', '1712167672', 'D0z6dLRTSw.u7tct9zQVBUOCBhPEiFn2Eb./li.oyUA' )" \
   | sqlite3 var/www/bidrag.db

RUN chmod a+w var/www/bidrag.db
EXPOSE 82
CMD httpd -p 82 -h /var/www -f -vv

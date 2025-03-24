#!/bin/sh

DB=/var/www/pseudonym/pseudonym.db

echo 'Access-Control-Allow-Origin: http://localhost:8080'
echo 'Access-Control-Allow-Credentials: true'
echo 'Access-Control-Allow-Methods: GET,POST,PUT,DELETE'
echo 'Access-Control-Allow-Headers: Content-Type'

echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=$HTTP_CONTENT_LENGTH$CONTENT_LENGTH

KR=$(head -c "$CONTENT_LENGTH" )

# Til loggen (kubctl logs pods/allpodd -c pseudonym-db -f)
echo psudonym-db fikk dette i kroppen: $KR >&2 

E=$( echo "$KR" | xmllint --xpath "/pseudonym/epost/text()"   -  2> /dev/null)
P=$( echo "$KR" | xmllint --xpath "/pseudonym/passord/text()" -  2> /dev/null)


# Henter lagret saltverdi
S=$( sqlite3 $DB "SELECT salt FROM Pseudonym WHERE epost='$E'" )
if [ "$S" = "" ]; then echo Salt mangler, finnes $E? >&2 ; exit; fi

# Beregner hashverdi av innsendt passord
H1=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )


# Sammenligner med lagret hashverdi
H2=$( sqlite3 $DB "SELECT passordhash FROM Pseudonym WHERE epost='$E'" )
if [ "$H1" != "$H2" ]; then echo Feil passord! >&2 ; exit; fi

# Returnerer pseudonym
PN=$(echo "SELECT pseudonym FROM  Pseudonym WHERE epost='$E'" | \
	 sqlite3  /var/www/pseudonym/pseudonym.db )
echo $PN >&2
echo $PN

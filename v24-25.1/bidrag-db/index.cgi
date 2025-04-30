#!/bin/sh

DB=/var/www/bidrag/bidrag.db
PKPATH=/var/www/bidrag/privatekeys
mkdir -p $PKPATH


# Skriver slutten av HTTP-hodet og en tom linje
cat <<EOF
Access-Control-Allow-Origin: http://localhost:8080
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,POST,PUT,DELETE
Access-Control-Allow-Headers: Content-Type
Content-Type:text/plain;charset=utf-8

EOF


# Omgår bug i httpd
CONTENT_LENGTH="${HTTP_CONTENT_LENGTH:-$CONTENT_LENGTH}"


if [ "$REQUEST_METHOD" = "OPTIONS" ]; then
    exit
else
    KR=$(head -c "$CONTENT_LENGTH" )

    # Til loggen (kubectl logs pods/allpodd -c bidrag-db -f)
    echo bidrag-db fikk dette i kroppen: $KR >&2

    N=$( echo "$KR" | xmllint --xpath "/bidrag/navn/text()"             - 2>/dev/null)
    P=$( echo "$KR" | xmllint --xpath "/bidrag/passord/text()"          - 2>/dev/null)
    K=$( echo "$KR" | xmllint --xpath "/bidrag/kommentar/text()"        - 2>/dev/null)
    O=$( echo "$KR" | xmllint --xpath "/bidrag/offentlig_nokkel/text()" - 2>/dev/null)
    T=$( echo "$KR" | xmllint --xpath "/bidrag/tittel/text()"           - 2>/dev/null)
    X=$( echo "$KR" | xmllint --xpath "/bidrag/tekst/text()"            - 2>/dev/null)

fi


#Generate Persistent Encrypted Private Key for user if it doesn't already exist
PKF=$PKPATH/$N.pem
if [ -f $PKF ]; then
    echo -e "PKPATH Success: $PKF" >&2
else
    echo -e "PKPATH Fail: $PKF : No Key Found" >&2
    openssl genrsa -aes128 -passout pass:$P -out $PKF 2048
fi
#Derrives and saves the Public Key to a Variable as a String and in a temp file
PUBLIC_KEY_TEMP=$(mktemp /tmp/XXXXXXXXX.pem)
openssl rsa -in $PKF -passin pass:$P -pubout -out $PUBLIC_KEY_TEMP
O=$(cat $PUBLIC_KEY_TEMP)
#echo -e "This is O: \n$O" >&2




if [ "$REQUEST_METHOD" = "GET" ]; then
    if [ -n "$N" -a -n "$P" ]; then

        # Vask inputter, beskytter mot SQL-injection
        N=$(echo "$N" | sed "s/'/''/g")
        P=$(echo "$P" | sed "s/'/''/g")    

        # Henter lagret saltverdi
        S=$(sqlite3 $DB "SELECT salt FROM Bidrag WHERE pseudonym='$N'")
        
        

        if [ -n "$S" ]; then
            echo "Feil: Salt mangler for pseudonym $N" >&2
            # Beregner hashverdi av innsendt passord
            H1=$(mkpasswd -m sha-256 -S $S $P | cut -f4 -d$)

            # Sammenligner med lagret hashverdi
            H2=$(sqlite3 $DB "SELECT passordhash FROM Bidrag WHERE pseudonym='$N'")
            if [ "$H1" != "$H2" ]; then
                echo "Feil: Ugyldig passord for pseudonym $N" >&2
                exit 1
            fi

            # Hent brukerens offentlige nøkkel og kryptert data
            ENCRYPTED_K=$(sqlite3 $DB "SELECT kommentar FROM Bidrag WHERE pseudonym='$N'")
            CLEAN_ENCRYPTED_K=$(echo $ENCRYPTED_K | base64 -d)

            # Dekrypter data med privat nøkkel
            DECRYPTED_K=$(echo "$ENCRYPTED_K" | base64 -d | openssl pkeyutl -decrypt -passin pass:$P -inkey $PKF )
            

            # logger dekryptert data
            echo -e "\nDekryptert data:\n$DECRYPTED_K\n" >&2
            echo -e "\nKryptert data:\n$ENCRYPTED_K\n" >&2
            echo -e "\CLEAN_ENCRYPTED_K:\n$CLEAN_ENCRYPTED_K\n" >&2
            # Query med union for å hente kommentaren til bruker i tillegg til andre sine bidrag
            

        
            QUERY="
            SELECT tittel, tekst, ' $DECRYPTED_K' AS kommentar\
            FROM Bidrag 
            WHERE pseudonym='$N'
            UNION 
            SELECT tittel, tekst, 'Hemmelig' AS kommentar
            FROM Bidrag 
            WHERE NOT pseudonym='$N'"

            # Logger bruker innlogging
            echo -e "\nLogging: \nBrukt Pseudonym = $N" >&2
        else
            # Query for alle uten kommentar, inkudert om salt manger (Alså logget inn bruker ikke har et innlegg)
            QUERY="SELECT tittel, tekst FROM Bidrag"
        fi
    else
        # Query for alle uten kommentar
        QUERY="SELECT tittel, tekst FROM Bidrag"
    fi

    # Kjører queryen
    RESULT=$(sqlite3 -line $DB "$QUERY" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "Feil: Mislykket å kjøre Query" >&2
        exit 1
    fi
    exit
fi


if [ "$N" = "" ]; then echo Pseudonym mangler! N: $N; exit; fi


if [ "$REQUEST_METHOD" = "POST" ]; then

    if [ "$N" != ""  -a  "$P" != "" ]; then

    # Krypter data med den genererte offentlige nøkkelen
    ENCRYPTED_K=$(echo $K | openssl pkeyutl -encrypt -pubin -inkey $PUBLIC_KEY_TEMP | base64)
    CLEAN_ENCRYPTED_K=$(echo $K | openssl pkeyutl -encrypt -pubin -inkey $PUBLIC_KEY_TEMP )
    echo -e "Encrypted K B64: \n$ENCRYPTED_K\n" >&2
    echo -e "CLEAN_ENCRYPTED_K: \n$CLEAN_ENCRYPTED_K\n" >&2
	# Lager et tilfeldig 11-sifret tall som salt
	S=$( for I in $(seq 11);do echo -n $(($RANDOM%9));done )

	# Lager en hashverdi av det skapte saltet og det innsendte passordet
	H=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )

	# Sett inn ny post i databasen
    sqlite3 $DB "INSERT INTO Bidrag (pseudonym, salt, passordhash, kommentar, offentlig_nokkel, tittel, tekst) \
                    VALUES ('$N', '$S', '$H', '$ENCRYPTED_K', '$O', '$T', '$X')"
    fi
    exit
fi

# Henter lagret saltverdi
S=$( sqlite3 $DB "SELECT salt FROM Bidrag WHERE pseudonym='$N'" )
if [ "$S" = "" ]; then echo Salt mangler ; exit; fi

# Beregner hashverdi av innsendt passord
H1=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )

# Sammenligner med lagret hashverdi
H2=$( sqlite3 $DB "SELECT passordhash FROM Bidrag WHERE pseudonym='$N'" )
if [ "$H1" != "$H2" ]; then echo Feil passord! >&2 ; exit; fi


if [ "$REQUEST_METHOD" = "DELETE" ]; then
    if [ "$N" != "" ]; then
	sqlite3 $DB "DELETE FROM Bidrag WHERE pseudonym='$N'"
    fi

elif [ "$REQUEST_METHOD" = "PUT" ]; then
    if [ "$N" = ""]; then
        exit
    fi
    NEW_ENCRYPTED_K=$(echo $K | openssl pkeyutl -encrypt -pubin -inkey $PUBLIC_KEY_TEMP | base64)
    echo -e "NEW Encrypted K: \n$NEW_ENCRYPTED_K\n" >&2
    # Oppdater databasen med den nye offentlige nøkkelen og kryptert data
    sqlite3 $DB \
    "UPDATE Bidrag SET kommentar='$NEW_ENCRYPTED_K',\
    tittel='$T', \
    tekst='$X' \
    WHERE pseudonym='$N'"
fi

rm -f $PUBLIC_KEY_TEMP
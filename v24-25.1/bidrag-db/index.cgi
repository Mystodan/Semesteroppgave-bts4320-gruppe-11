#!/bin/sh

DB=/var/www/bidrag/bidrag.db

# Skriver slutten av HTTP-hodet og en tom linje
cat <<EOF
Access-Control-Allow-Origin: http://localhost:8080
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,POST,PUT,DELETE
Access-Control-Allow-Headers: Content-Type
Content-Type:text/plain;charset=utf-8

EOF

# Funksjon for RSA-kryptering
rsa_encrypt() {
    echo "$1" | openssl pkeyutl -encrypt -pubin -inkey <(echo "$2") -out /dev/stdout | base64
}

# Funksjon for RSA-dekryptering
rsa_decrypt() {
    echo "$1" | base64 -d | openssl pkeyutl -decrypt -inkey "$2"
}

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
            PUBLIC_KEY=$(sqlite3 $DB "SELECT offentlig_nokkel FROM Bidrag WHERE pseudonym='$N'")
            ENCRYPTED_K=$(sqlite3 $DB "SELECT kommentar FROM Bidrag WHERE pseudonym='$N'")

            # Dekrypter data med privat nøkkel
            PRIV_KEY_PATH="/var/www/cgi-bin/private_keys"
            DECRYPTED_K=$(rsa_decrypt "$ENCRYPTED_K", "$PRIV_KEY_PATH/$N.pem")

            # logger dekryptert data
            echo -e "\nDekryptert data: \nKommentar = $DECRYPTED_K" >&2
            echo -e $PWD >&2
            # Query med union for å hente kommentaren til bruker i tillegg til andre sine bidrag
        
            QUERY="SELECT tittel, tekst, '$DECRYPTED_K' AS kommentar FROM Bidrag WHERE pseudonym='$N' UNION SELECT tittel, tekst, 'Utilgjengelig for denne brukeren' AS kommentar FROM Bidrag WHERE NOT pseudonym='$N'"

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

    # utgir resultatet
    echo "$RESULT"
    exit
fi


if [ "$N" = "" ]; then echo Pseudonym mangler!; exit; fi


if [ "$REQUEST_METHOD" = "POST" ]; then

    if [ "$N" != ""  -a  "$P" != "" ]; then

    # Generer et nytt RSA-nøkkelpar for brukeren
    PRIVATE_KEY_FILE=$(mktemp)
    PUBLIC_KEY_FILE=$(mktemp)
    openssl genrsa -out "$PRIVATE_KEY_FILE" 2048
    openssl rsa -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE"

    # importer nøklene inn i variabler
    PRIVATE_KEY=$(cat "$PRIVATE_KEY_FILE")
    PUBLIC_KEY=$(cat "$PUBLIC_KEY_FILE")

    # Fjern midlertidige filer
    rm -f "$PRIVATE_KEY_FILE" "$PUBLIC_KEY_FILE"

    # Krypter data med den genererte offentlige nøkkelen
    ENCRYPTED_K=$(rsa_encrypt "$K" "$PUBLIC_KEY")

	# Lager et tilfeldig 11-sifret tall som salt
	S=$( for I in $(seq 11);do echo -n $(($RANDOM%9));done )

	# Lager en hashverdi av det skapte saltet og det innsendte passordet
	H=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )

	# Sett inn ny post i databasen
    sqlite3 $DB "INSERT INTO Bidrag (pseudonym, salt, passordhash, kommentar, offentlig_nokkel, tittel, tekst) \
                    VALUES ('$N', '$S', '$H', '$ENCRYPTED_K', '$PUBLIC_KEY', '$T', '$X')"

    # Lagre den private nøkkelen sikkert
    mkdir -p private_keys
    echo "$PRIVATE_KEY" > "private_keys/$N.pem"
    chmod 600 "private_keys/$N.pem"
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
    # Oppdater databasen med den nye offentlige nøkkelen og kryptert data
    sqlite3 $DB \
    "UPDATE Bidrag SET kommentar='$NEW_ENCRYPTED_K',
    offentlig_nokkel='$O',
    tittel='$T', 
    tekst='$X' 
    WHERE pseudonym='$N'"
fi


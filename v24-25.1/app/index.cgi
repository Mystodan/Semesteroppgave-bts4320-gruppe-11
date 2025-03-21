#!/bin/sh
echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=$HTTP_CONTENT_LENGTH$CONTENT_LENGTH

# Henter data fra HTTP-kpppen 
KROPP=$(head -c "$CONTENT_LENGTH")

# Fikser alfakrøll (intet annet)
KROPP=$(echo $KROPP|sed "s/%40/@/")

# Til loggen (kubctl logs pods/allpodd -c app -f)
echo app fikk dette i kroppen: $KROP >&2


# Fordeler inndataene i variabler
for I in $(echo $KROPP|tr '&' ' '); do

    N=$(echo "$I"|cut -f1 -d=)
    V=$(echo "$I"|cut -f2 -d=)

    if [ "$N" = "epost"             ]; then  E="$V"; fi  
    if [ "$N" = "passord"           ]; then  P="$V"; fi  
    if [ "$N" = "kommentar"         ]; then  K="$V"; fi
    if [ "$N" = "offentlig_nokkel"  ]; then  O="$V"; fi
    if [ "$N" = "tittel"            ]; then  T="$V"; fi
    if [ "$N" = "tekst"             ]; then  X="$V"; fi
    if [ "$N" = "handling"          ]; then  H="$V"; fi  

done

## 1. HENTER PSEUDONYM ##

# Dataene skal sendes i XML-format til pseudonym-databasen
XML="<pseudonym>             \
        <epost>$E</epost>    \
       <passord>$P</passord> \
     </pseudonym>"

# URL til pseudonym-databasen
URL='allpodd:83' 

# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
KROPP: $KROPP
PN-URL:   $URL
PN-XML:
$XML
EOF


# Henter pseudonym
N=$(curl -s -d "$XML" $URL)


## 1. KONTAKTER BIDRAG-DB ##

# Dataene skal sendes i XML-format til bidrag-databasen
XML="<bidrag>\
<navn>$N</navn>\
<passord>$P</passord>\
<kommentar>$K</kommentar>\
<offentlig_nokkel>$O</offentlig_nokkel>\
<tittel>$T</tittel>\
<tekst>$X</tekst>\
</bidrag>"

# URL til bidrag-databasen
URL='allpodd:82' 


# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett" ]; then curl -s -X DELETE -d "$XML" $URL; fi     
if [ "$H" = "Endre" ]; then curl -s -X PUT    -d "$XML" $URL; fi
if [ "$H" = "Ny"    ]; then curl -s -X POST   -d "$XML" $URL; fi
if [ "$H" = "Liste" ]; then curl -s -X GET    -d "$XML" $URL; fi


# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
BIDRAG-URL:   $URL
BIDRAG-XML:
$XML
EOF

#!/bin/bash

# Et skript for å lage lokale databaser brukt av allpodd.
# Dette skriptet funker også som et reset skript ved å kjøre det på nytt.
#
# Databasene blir plassert i hver sin katalog.
#
# I katalogen /var/www/bidrag blir bidrag.db plassert.
# I katalogen /var/www/pseudonym blir pseudonym.db plassert.

# ========================
# Bidrag database oppsett.
# ========================

DB_NAME="bidrag.db"

# Fjerner bidrag db.
sudo rm /var/www/bidrag/"$DB_NAME"

# Lager bidrag katalogen.
sudo mkdir /var/www/bidrag

# Lager bidrag databasen.
sudo sqlite3 "$DB_NAME" <<EOF
DROP TABLE IF EXISTS Bidrag;
CREATE TABLE Bidrag (                  
  pseudonym        VARCHAR(200) PRIMARY KEY, 
  salt             VARCHAR(11),              	
  passordhash      VARCHAR(44),              
  kommentar        VARCHAR(1000),            
  offentlig_nokkel VARCHAR(200),            
  tittel           VARCHAR(100),             
  tekst            VARCHAR(1000)
);
EOF

# Setter inn eksempel data i Bidrag tabellen.
sudo sqlite3 "$DB_NAME" <<EOF
INSERT INTO Bidrag (pseudonym, salt, passordhash) VALUES                 
   ('osiedahs', '1712167670', 'Aw16YyLRWTS0BOoOb7DpvBMeYb444g.kl1a542GYpJA' ),
   ('uozaixav', '1712167671', 'q37QpOdM2jSDeXOVAyiCSzMgy08dI7pLQ1aBElJps48' ), 
   ('olaebaev', '1712167672', 'D0z6dLRTSw.u7tct9zQVBUOCBhPEiFn2Eb./li.oyUA' );
EOF

# Gir alle brukere skrive tilgang på bidrag db.
sudo chmod a+w "$DB_NAME"

# Flytter bidrag db til /var/www/bidrag.
sudo mv ./$DB_NAME /var/www/bidrag

echo "Database '$DB_NAME' laget og befolket suksessfullt!"

# ===========================
# Pseudonym database oppsett. 
# ===========================

DB_NAME="pseudonym.db"

# Fjerner pseudonym db.
sudo rm /var/www/pseudonym/"$DB_NAME"

# Lager pseudonym katalogen.
sudo mkdir /var/www/pseudonym

# Lager pseudonym databasen.
sudo sqlite3 "$DB_NAME" <<EOF
DROP TABLE IF EXISTS Pseudonym;
CREATE TABLE Pseudonym (           
  epost         VARCHAR(200) PRIMARY KEY, 
  pseudonym     VARCHAR(200),             
  salt          VARCHAR(11),              	
  passordhash   VARCHAR(44)
);
EOF

# Setter inn eksempel data i pseudonym tabellen.
sudo sqlite3 "$DB_NAME" <<EOF
INSERT INTO Pseudonym (epost, pseudonym, salt, passordhash) VALUES                
   ('Ante@example.com'   ,'osiedahs', '1712167670', 'Aw16YyLRWTS0BOoOb7DpvBMeYb444g.kl1a542GYpJA' ), 
   ('Bjart@example.com'  ,'uozaixav', '1712167671', 'q37QpOdM2jSDeXOVAyiCSzMgy08dI7pLQ1aBElJps48' ), 
   ('Cecilie@example.com','olaebaev', '1712167672', 'D0z6dLRTSw.u7tct9zQVBUOCBhPEiFn2Eb./li.oyUA' );
EOF

# Gir alle brukere skrive tilgang på pseudonym db.
sudo chmod a+w "$DB_NAME"

# Flytt pseudonym db til /var/www/pseudonym.
sudo mv ./$DB_NAME /var/www/pseudonym

echo "Database '$DB_NAME' laget og befolket suksessfullt!"

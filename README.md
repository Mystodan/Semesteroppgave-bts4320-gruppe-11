# BTS4320 Gruppe 11 - Semesteroppgave
Av: Christoffer Simonsen, Daniel Hao Huynh, Emil-Alexander Thoresen Motrøen, Mikael Fossli
#### Spesifikasjoner
https://debbie.usn.no/bts4320/#prosjektoppgave 

## Kjøring av prosjektet
Aller først ``cd gå/til/prosjekt/stien``

Først kjør ``sudo ./create_host_db.sh`` for å initalisere databasene.

Kjør ``sudo ./create_admin_users.sh`` for å sette opp adminstratorer og navnrom.

Så kjør ``sudo ./podman_til_k8s.sh`` for å bygge og starte prosjektet.

Hvis port-forward feiler på grunn av sertifikat så er det mulig å kjøre ``./refresh_certs.sh`` skriptet.

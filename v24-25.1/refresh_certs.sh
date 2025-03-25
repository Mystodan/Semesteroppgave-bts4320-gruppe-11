#!/bin/bash

# Kjør dette skriptet om man får problemer med sertifiseringer etter man har prøvd å port-forward.

# Lager nye sertifiseringer og overskriver kubernetes konfigurasjonen.
sudo microk8s refresh-certs -e ca.crt

# Hvis det ikke hjelper med kommandoen over, så prøv kommandoen under.
# microk8s config > ~/.kube/config

echo "Hvil du port-forward service/allpodd på 80 og 81 (y/n)?"
read answer

if [ $answer = "y" ]; then
    # Gjør web(80) og app(81) tilgjengelig på localhost.
    microk8s kubectl port-forward service/allpodd 8080:81 &
    microk8s kubectl port-forward service/allpodd 8080:80 &
fi
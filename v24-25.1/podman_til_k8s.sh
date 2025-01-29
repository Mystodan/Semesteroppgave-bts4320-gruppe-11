#!/bin/sh 
# gcc -static -o db/db db/db.c

# Rydder opp (ved å drepe og fjerne podden)
podman pod kill allpodd
podman pod rm   allpodd


# Bygger konteiner-bilder i Podmans konteinerbildearkiv
podman build pseudonym-db -t pseudonym-db
podman build bidrag-db    -t bidrag-db
podman build app          -t app
podman build web          -t web


# Overfører bilder fra Podman til Kubernates
# Referamser:
# - https://docs.podman.io/en/latest/markdown/podman-save.1.html
# - https://microk8s.io/docs/registry-images

podman save  pseudonym-db:latest | microk8s ctr image import -
podman save  bidrag-db:latest    | microk8s ctr image import -
podman save  app:latest          | microk8s ctr image import -
podman save  web:latest          | microk8s ctr image import -

# Oppretter Podmman-podd
podman  pod create --name allpodd -p 8080:80 -p 8081:81

# Starter konteinere, basert på konternerbildene, i den opprettede
# podden.
podman run -dit --pod=allpodd --restart=always --name app          localhost/app
podman run -dit --pod=allpodd --restart=always --name bidrag-db    localhost/bidrag-db
podman run -dit --pod=allpodd --restart=always --name pseudonym-db localhost/pseudonym-db
podman run -dit --pod=allpodd --restart=always --name web          localhost/web


# Lager kubernetes-fil
rm ./allpodd.yaml
podman generate kube allpodd --service -f ./allpodd.yaml

# Erstatt nodePort verdien etter navn: "80"
sed -i '/- name: "80"/!b;n;s/nodePort: [0-9]\+/nodePort: 30080/' allpodd.yaml

# Erstatt nodePort verdien etter navn: "81"
sed -i '/- name: "81"/!b;n;s/nodePort: [0-9]\+/nodePort: 30081/' allpodd.yaml

# imagePullPolicy: Never
sed -i "/image:/a \    imagePullPolicy: Never" allpodd.yaml

# Rydder opp (ved å drepe og fjerne podden)
podman pod kill allpodd
podman pod rm   allpodd


# Stoppper kjørende service og pod
microk8s kubectl delete service/allpodd
microk8s kubectl delete pod/allpodd

# Starte podden i en Service i K8S
microk8s kubectl create -f allpodd.yaml
microk8s kubectl get all

echo "Gjør web (80) og app (81) tilgjengelig på localhost:"
echo  microk8s kubectl port-forward service/allpodd 8080:80 &
echo  microk8s kubectl port-forward service/allpodd 8081:81 &

# Starter podden i Podman: "
# podman kube play allpodd.yaml

#!/bin/sh 

# Rydder opp (ved å drepe og fjerne podden)
podman pod kill allpodd
podman pod rm   allpodd

# =======================================================
# Bygger konteiner-bilder i Podmans konteinerbildearkiv      
# med komandoer på følgende form:                            
#                                                            
# podman build <katalog> -t <bildenavn>                      
# =======================================================

podman build pseudonym-db -t pseudonym-db
podman build bidrag-db    -t bidrag-db
podman build app          -t app
podman build web          -t web

# ===============================================================
# Overfører bilder fra Podman til Kubernates
# Referanser:
# - https://docs.podman.io/en/latest/markdown/podman-save.1.html
# - https://microk8s.io/docs/registry-images
# ===============================================================

podman save  pseudonym-db:latest | microk8s ctr image import -
podman save  bidrag-db:latest    | microk8s ctr image import -
podman save  app:latest          | microk8s ctr image import -
podman save  web:latest          | microk8s ctr image import -

# ========================================================
# Lager og redigerer filen allpodd.yaml som brukes til å 
# iverksette systemet i kubernetes (microk8s)
# ========================================================

# Oppretter Podmman-podd
podman  pod create --name allpodd -p 8080:80 -p 8081:81

# Starter konteinere, basert på konternerbildene, i den opprettede
# podden.
podman run -dit --pod=allpodd --restart=always --name app          localhost/app
podman run -dit --pod=allpodd --restart=always --name bidrag-db    localhost/bidrag-db
podman run -dit --pod=allpodd --restart=always --name pseudonym-db localhost/pseudonym-db
podman run -dit --pod=allpodd --restart=always --name web          localhost/web

# Sletter gammel kubernetes-fil -- om den finnes
rm -f ./allpodd.yaml

# Lager kubernetes-fil
podman generate kube allpodd --service -f ./allpodd.yaml

# Erstatt nodePort verdien etter navn: "80"
sed -i '/- name: "80"/!b;n;s/nodePort: [0-9]\+/nodePort: 30080/' allpodd.yaml

# Erstatt nodePort verdien etter navn: "81"
sed -i '/- name: "81"/!b;n;s/nodePort: [0-9]\+/nodePort: 30081/' allpodd.yaml

# imagePullPolicy: Never
# Ref: https://stackoverflow.com/questions/37302776/what-is-the-meaning-of-imagepullback-status-on-a-kube
sed -i "/image:/a \    imagePullPolicy: Never" allpodd.yaml

# Setter inn volumes under "spec:".
sed -i '$a\
  volumes:\
    - name: "bidrag-data"\
      persistentVolumeClaim:\
        claimName: bidrag-pvc\
    - name: "pseudonym-data"\
      persistentVolumeClaim:\
        claimName: pseudonym-pvc' allpodd.yaml

# Setter inn volumeMounts under bidrag-db konteineren.
sed -i '/name: bidrag-db/a\
    volumeMounts:\
        - mountPath: "/var/www/bidrag"\
          name: "bidrag-data"' allpodd.yaml

# Setter inn volumeMounts under pseudonym-db konteineren.
sed -i '/name: pseudonym-db/a\
    volumeMounts:\
        - mountPath: "/var/www/pseudonym"\
          name: "pseudonym-data"' allpodd.yaml

# Legg til persistent volume og claims for bidrag- og pseudonym-db.
cat pv_and_pvc.yaml >> allpodd.yaml

# Rydder opp (ved å drepe og fjerne podden)
podman pod kill allpodd
podman pod rm   allpodd

# ======================
# Starter opp systemtet
# ======================

# Stoppper kjørende service og pod
microk8s kubectl delete service/allpodd
microk8s kubectl delete pod/allpodd

# Sletter PersistentVolume og PersistentVolumeClaims for bidrag og pseudonym databasene.
microk8s kubectl delete pv bidrag-pv &
microk8s kubectl delete pvc bidrag-pvc &
microk8s kubectl delete pv pseudonym-pv &
microk8s kubectl delete pvc pseudonym-pvc &

# Starte podden i en Service i K8S
microk8s kubectl create -f allpodd.yaml
microk8s kubectl get all

# Hent persistentvolume og claims. 
# microk8s kubectl get pv
# microk8s kubectl get pvc

# =================================================
# Skriver ut info for tilgang på lokal vertsmaskin
# =================================================

echo
echo
echo "Gjør web (80) og app (81) tilgjengelig på localhost:"
echo
echo "microk8s kubectl port-forward service/allpodd 8080:80 &"
echo "microk8s kubectl port-forward service/allpodd 8081:81 &"
echo
echo "For å se i nettleser, gå til http://localhost:8080"
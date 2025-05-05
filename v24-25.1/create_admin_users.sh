#Skrur på Role Based Access Control (RBAC)
microk8s enable rbac

#Sjekker at RBAC ble skrudd på. rbac skal være listet under addons -> enabled -> rbac
#microk8s status

#Lager navnerom for bidrag- og pseudonym konteinerne
kubectl create namespace pseudonymrom
kubectl create namespace bidragsrom

#Lager admin roller for navnerommene
kubectl create role pseudonymadminrolle --verb='*' --resource='*' -n=pseudonymrom
kubectl create role bidragsadminrolle   --verb='*' --resource='*' -n=bidragsrom

#Verifiserer at rollene er riktige
#kubectl get roles -n pseudonymrom
#kubectl get roles -n bidragsrom

#Lager rollebindinger til grupper
kubectl create rolebinding pseudonymbinding --role=pseudonymadminrolle --group=pseudonymadmingruppe -n=pseudonymrom
kubectl create rolebinding bidragsbinding --role=bidragsadminrolle --group=bidragsadmingruppe -n=bidragsrom

#4b - Verifiserer at rollebindigene ble skapt riktig
#kubectl get rolebindings -n pseudonymrom
#kubectl get rolebindings -n bidragsrom
#eller
#kubectl get rolebindings -n pseudonymrom -o yaml
#kubectl get rolebindings -n bidragsrom -o yaml


KeysPath="./adminkeys"
mkdir $KeysPath

#Lager nøkkler til administratorene
openssl genrsa 2048 > "$KeysPath/arne.key"
openssl genrsa 2048 > "$KeysPath/beate.key"

#Lager signeringsforesprlser som skal i yaml filen, disse er kodet til base64
openssl req -new -key arne.key  -subj "/CN=arne/O=pseudonymadmingruppe" | base64 | tr -d '\n' > "$KeysPath/arneb64.txt"
openssl req -new -key beate.key -subj "/CN=beate/O=bidragsadmingruppe"  | base64 | tr -d '\n' > "$KeysPath/beateb64.txt"

#Putter innholdet fra arneb64.txt of beateb64.txt inn i yaml filen under

cat <<EOF > $KeysPath/signeringsforesporsel.yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: arne-csr
spec:
  request: $(cat "$KeysPath/arneb64.txt")
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages:
    - client auth
--- 
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: beate-csr
spec:
  request: $(cat "$KeysPath/beateb64.txt")
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages:
    - client auth
EOF

#Iverksetter singeringforespørselene
kubectl apply -f $KeysPath/signeringsforesporsel.yaml

#Godkjenner signeringsforespørslene
kubectl certificate approve arne-csr
kubectl certificate approve beate-csr

kubectl config set-credentials arne --client-key=$KeysPath/arne.key --client-certificate=$KeysPath/arne.key --embed-certs=true
kubectl config set-credentials beate --client-key=$KeysPath/beate.key --client-certificate=$KeysPath/beate.crt --embed-certs=true

if [ $? -ne 0 ]; then
	echo "An error occured"
	exit 1
else
	echo "Users Arne and Beate created successfully"
fi
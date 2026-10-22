#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
IMAGE="us.icr.io/$(oc project -q)/accounts:1"
echo "Lab image: $IMAGE"
docker build -t "$IMAGE" . 2>&1 | tee evidence/docker-build.txt
docker run --rm --user 0 -v "$PWD:/workspace" -w /workspace -e DATABASE_URI=sqlite:////tmp/accounts-tests.db "$IMAGE" sh -c 'flake8 service tests && nosetests -v --with-spec --spec-color' 2>&1 | tee evidence/ci-workflow-done
cp evidence/ci-workflow-done evidence/security-headers-done
docker run -d --name capstone-accounts -p 8080:8080 -e DATABASE_URI=sqlite:////tmp/accounts.db "$IMAGE"
for attempt in $(seq 1 30); do curl -fsS http://localhost:8080/health && break || sleep 2; done
capture() {
  local file="$1"; shift
  { printf '$ '; printf '%q ' "$@"; printf '\n'; "$@"; printf '\n'; } 2>&1 | tee "evidence/$file"
}
capture kube-app-output curl -sS -i http://localhost:8080/
capture rest-create-done curl -sS -i -X POST -H 'Content-Type: application/json' -d '{"name":"John Doe","email":"john@example.com","address":"123 Main St","phone_number":"123-456-7890","date_joined":"2023-01-01"}' http://localhost:8080/accounts
capture rest-read-done curl -sS -i -X GET http://localhost:8080/accounts/1
capture rest-list-done curl -sS -i -X GET http://localhost:8080/accounts
capture rest-update-done curl -sS -i -X PUT -H 'Content-Type: application/json' -d '{"name":"Jane Doe","email":"john@example.com","address":"123 Main St","phone_number":"123-456-7890","date_joined":"2023-01-01"}' http://localhost:8080/accounts/1
capture rest-delete-done curl -sS -i -X DELETE http://localhost:8080/accounts/1
docker images --filter "reference=$IMAGE" | tee evidence/kube-images
ibmcloud cr login
kubectl create secret generic capstone-registry --type=kubernetes.io/dockerconfigjson --from-file=.dockerconfigjson="$HOME/.docker/config.json" --dry-run=client -o yaml | kubectl apply -f -
docker push "$IMAGE" 2>&1 | tee evidence/docker-push.txt
if ! oc get service postgresql >/dev/null 2>&1; then
  oc new-app --template=postgresql-ephemeral --param=DATABASE_SERVICE_NAME=postgresql --param=POSTGRESQL_USER=postgres --param=POSTGRESQL_PASSWORD=postgres --param=POSTGRESQL_DATABASE=postgres
fi
kubectl create secret generic accounts-db --from-literal=database-uri=postgresql://postgres:postgres@postgresql:5432/postgres --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/
kubectl set image deployment/accounts accounts="$IMAGE"
kubectl rollout status deployment/accounts --timeout=180s
kubectl get all | tee evidence/kube-deploy-accounts
if ! oc get route accounts >/dev/null 2>&1; then oc expose service/accounts; fi
kubectl apply -f tekton/tasks.yaml -f tekton/pipeline.yaml
oc policy add-role-to-user edit "system:serviceaccount:$(oc project -q):pipeline"
kubectl create -f tekton/pipelinerun.yaml | tee evidence/pipelinerun-created.txt
tkn pipelinerun logs --last -f 2>&1 | tee evidence/pipelinerun.txt
tkn pipelinerun describe --last | tee evidence/pipelinerun-status.txt

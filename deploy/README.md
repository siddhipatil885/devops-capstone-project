# Deployment prerequisites

Use the lab namespace and authenticated IBM Container Registry. Build and push the image before applying the manifests. If your lab's registry namespace differs, replace the image in `deployment.yaml` with your authorized namespace.

Provision the IBM starter PostgreSQL template, then create the connection secret (the credentials below are disposable lab examples):

```sh
oc new-app --template=postgresql-ephemeral --param=DATABASE_SERVICE_NAME=postgresql --param=POSTGRESQL_USER=postgres --param=POSTGRESQL_PASSWORD=postgres --param=POSTGRESQL_DATABASE=postgres
kubectl create secret generic accounts-db --from-literal=database-uri=postgresql://postgres:postgres@postgresql:5432/postgres
kubectl apply -f deploy/
kubectl rollout status deployment/accounts --timeout=180s
oc expose service/accounts
```

The database is ephemeral for this course lab. Use persistent storage and managed credentials for production.

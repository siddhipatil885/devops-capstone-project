# Accounts REST API

[![CI Build](https://github.com/siddhipatil885/devops-capstone-project/actions/workflows/ci-build.yaml/badge.svg)](https://github.com/siddhipatil885/devops-capstone-project/actions/workflows/ci-build.yaml)

An account lifecycle microservice for the IBM DevOps and Software Engineering capstone. Based on IBM's Apache-2.0 licensed [official starter](https://github.com/ibm-developer-skills-network/aolwx-devops-capstone-template).

Accounts contain name, email, address, optional phone number, and date joined. PostgreSQL persists data. Flask-Talisman supplies security headers and Flask-CORS supports cross-origin requests.

| Method | Path | Result |
| --- | --- | --- |
| POST | /accounts | Create, 201 and Location header |
| GET | /accounts | List, 200 (optional name filter) |
| GET | /accounts/{id} | Read, 200 or 404 |
| PUT | /accounts/{id} | Update, 200 or 404 |
| DELETE | /accounts/{id} | Delete, 204 (idempotent) |
| GET | /health | Health check, 200 |

## Development

Use Python 3.9 for the course's legacy nose runner. Start PostgreSQL and set `DATABASE_URI` to your database connection URI. For isolated local smoke tests, `DATABASE_URI=sqlite:////tmp/accounts.db` is also supported.

```sh
python -m pip install -r requirements.txt
flake8 service tests
nosetests -v --with-spec --spec-color
gunicorn --bind=0.0.0.0:8080 service:app
```

`setup.cfg` enforces at least 95% service coverage. GitHub Actions runs the linter and tests against PostgreSQL on every push and pull request to main.

## Deployment

```sh
docker build -t us.icr.io/sn-labs-siddhipatil2/accounts:1 .
docker push us.icr.io/sn-labs-siddhipatil2/accounts:1
kubectl apply -f deploy/
kubectl rollout status deployment/accounts
```

Provide the PostgreSQL Secret described in `deploy/README.md` first. The runtime user is non-root. The ingress supplies TLS; local HTTP is supported on port 8080.

See `tekton/README.md` for the pipeline setup and execution. Evidence files are kept separately in `evidence/`; screenshots and run logs must come from real executions. Configuration presence alone does not prove deployment success.


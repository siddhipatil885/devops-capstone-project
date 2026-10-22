# Tekton CD pipeline

The lab must provide Tekton/OpenShift Pipelines, the buildah ClusterTask, registry access for the pipeline service account, and the accounts-db Secret. Configure a registry namespace you own in the PipelineRun. Give the pipeline service account the namespace edit role for deployment. Buildah uses the repo subdirectory containing the Dockerfile.

```sh
ibmcloud cr login
kubectl create secret generic capstone-registry --type=kubernetes.io/dockerconfigjson --from-file=.dockerconfigjson="$HOME/.docker/config.json"
oc policy add-role-to-user edit system:serviceaccount:$(oc project -q):pipeline
kubectl apply -f tekton/tasks.yaml -f tekton/pipeline.yaml
kubectl create -f tekton/pipelinerun.yaml
tkn pipelinerun logs --last -f
tkn pipelinerun describe --last
tkn pipelinerun logs --last > pipelinerun.txt
```

Each run gets a fresh workspace claim. The tasks clone main, lint, run tests with the 95% threshold, build and push with buildah, and wait for the actual application rollout. If the lab lacks the buildah ClusterTask, install the catalog task and update its taskRef. Do not claim success until the PipelineRun reports Succeeded=True.

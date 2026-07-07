# Mini Financial Terminal — Backend (Kubernetes Local Deployment)

This is a toy financial data terminal that pulls real-time stock quotes and income statement data from the [Financial Modeling Prep API](https://financialmodelingprep.com), displays the data in a tabular layout, and logs every query to a MongoDB instance. It's built as a learning project, not a product.

## What this is

This is the backend repo for the mini terminal. It's a FastAPI application that:
- handles API calls to Financial Modeling Prep

- caches results to avoid redundant calls
- computes a handful of derived financial metrics
- logs query metadata to MongoDB

The Streamlit frontend that actually renders the terminal interface lives in a [companion repo](https://github.com/jtolsma1/mini-terminal-frontend).

### Repo structure
- This repo contains multiple branches for teaching different aspects of containerized deployment.

- The main branch is the most recent teaching project and  is structured for **local Kubernetes deployment** using Minikube. 
    - The `kubernetes/` directory contains deployment and service manifests for the FastAPI backend and a MongoDB sidecar.
    - The backend and MongoDB run as separate Deployments connected via Kubernetes' internal DNS — `mongo-service` resolves to the MongoDB pod from within the cluster.
- There's also a `docker-compose.yaml` and a `notebooks/` directory left over from earlier stages of development. 

## Why it exists

- I built this app from scratch specifically to teach myself Docker and Kubernetes. 
- I sat down and deliberately designed an application that would give me something real to work with while going through a Docker and Kubernetes course. 
- The financial data angle was a conscious choice:
    - It's complex enough to be interesting (multiple API calls, caching logic, derived metrics, a database)
    - It's not so complex that the application itself would get in the way of learning the infrastructure

- This project is not meant to be taken seriously as production code:
    - There are no tests
    - The error handling is minimal
    - The financial metrics are illustrative rather than investment-grade

## If you really want to run it

You'll need a free API key from [Financial Modeling Prep](https://financialmodelingprep.com). 

Beyond that, you're on your own — there are no setup instructions here by design. If you're the kind of person who would actually want to run this, you probably know what to do with a Dockerfile and a `kubernetes/` directory.
# Taxi & Book Translation Platform

A powerful, containerized full-stack platform enabling **real-time taxi cluster visualization in Singapore** and a **fast, book-length translation service** using modern LLMs and public APIs. Built for scalability, cloud-native deployment, and developer extensibility.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Design Principles](#design-principles)
4. [Major API Integrations](#major-api-integrations)
5. [Environment Variables & API Keys](#environment-variables--api-keys)
6. [Setup & Deployment](#setup--deployment)
    - [Prerequisites](#prerequisites)
    - [Docker Compose (Local)](#docker-compose-local)
    - [Kubernetes & Minikube (Advanced/Prod)](#kubernetes--minikube-advancedprod)
7. [API Endpoints & Usage](#api-endpoints--usage)
8. [Future Improvements & Roadmap](#future-improvements--roadmap)
9. [Troubleshooting](#troubleshooting)
10. [File Structure](#file-structure)
11. [Contributing](#contributing)

---

## Introduction

This project is a multimodal web platform offering:
- **Taxi Availability Hotspot Visualization** for Singapore, using official live data
- **Book Translation Service** with support for long-form texts and multiple languages, powered by leading LLMs

The application is fully containerized (Docker) and orchestration-ready (Kubernetes), allowing for robust local or cloud-native deployment.

---

## Architecture & Tech Stack

- **Frontend:** React (TypeScript), Zustand state management, Nginx (static production server)
- **Backend:** Node.js (Express), serving REST API endpoints, forwarding to data/translation services
- **Translation Service:** FastAPI (Python), LLM-powered translation using HuggingFace Transformers and SEA-LION API
- **APIs Used:**  
  - OneMap (SG Taxi data)
  - SEA-LION (for advanced translation tasks)
- **DevOps:** Docker, Kubernetes (minikube), custom Nginx reverse proxy config for API routing

---

## Design Principles

- **Separation of Concerns:** Distinct microservices (frontend UI, backend API, translation worker)
- **12-Factor App:** Configuration via environment variables, stateless containers, repeatable builds
- **API-First:** Clean, well-documented REST endpoints
- **Extensible:** Simple to add new services or UI features
- **Scalable:** Kubernetes manifests included; suitable for Minikube & cloud

---

## Major API Integrations

- **OneMap:** For real-time taxi cluster data.  
  _Requires API key. Handles reverse geocoding and area cluster heatmapping._
- **SEA-LION:** LLM-based translation (HuggingFace).  
  _Translation engine for long-form/full book tasks, optional external SEA-LION API key._

---

## Environment Variables & API Keys

**You must supply valid API keys/tokens for external data and translation!**  
- `ONEMAP_API_ACCESS_TOKEN` _(required for taxi data)_
- `SEA_LION_API_KEY` _(optional, for enhanced LLM translation; may use HuggingFace locally as fallback)_

Set these in each service’s `.env` file or, for Kubernetes, as a `Secret` or plain `env` section of your deployment.

---

## Setup & Deployment

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) (Desktop/Engine)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [Minikube](https://minikube.sigs.k8s.io/docs/) (for Kubernetes-local dev)
- (Optional) [Docker Hub](https://hub.docker.com/) account for pushing images

---

### Docker Compose (Local)

1. **Clone this repo**
    ```
    git clone https://github.com/your-username/taxi-book-translation.git
    cd taxi-book-translation
    ```

2. **Configure .env files**  
   Place your API keys/secrets in:
   - `backend/.env`
   - `translation-service/.env`

3. **Build and start all services:**
    ```
    docker-compose up --build
    ```

4. **Access the app:**  
    - Go to [http://localhost:3000](http://localhost:3000) for the homepage
    - Taxi Hotspots: `/taxi-availability`
    - Translation Service: `/translate`

---

### Kubernetes & Minikube (Advanced/Prod)

1. **Start your Minikube cluster**
    ```
    minikube start
    ```

2. **(Optional) Build and push Docker images**  
    ```
    docker build -t <yourdockerhubuser>/mern-frontend:latest ./frontend
    docker build -t <yourdockerhubuser>/mern-backend:latest ./backend
    docker build -t <yourdockerhubuser>/fastapi-translation:latest ./translation-service
    ```
    Docker push for each


3. **Configure Secrets for API keys**  
    ```
    kubectl create secret generic onemap-secrets --from-literal=ONEMAP_API_ACCESS_TOKEN=your_token
    kubectl create secret generic sea-lion-secrets --from-literal=SEA_LION_API_KEY=your_sealion_key
    ```
    Reference these with `envFrom` or `env` in your deployment YAMLs.

4. **Apply manifests:**
    ```
    kubectl apply -f k8s/
    ```

5. **Access services:**
 - Use `minikube service <service-name>` to open services in your browser.

---


## API Endpoints & Usage

**Backend (Node/Express):**
- `/api/taxi-availability/top` &rarr;  [GET] Top taxi cluster locations (uses OneMap & reverse geocode)
- `/api/translate_book` &rarr; [POST] Submit a book translation job (forwards to FastAPI worker)

**Translation Service (FastAPI):**
- `/translate` &rarr; [POST] Translate book text (supports SEA-LION/HuggingFace)

_Your API keys must be valid or you will see authorization errors from OneMap/SEA-LION endpoints!_

---

## Future Improvements & Roadmap

- **Authentication layer** (User login, JWT-based API security)
- **Job status polling & progress UI** for translations
- **SG taxi heatmap visualization**
- **Multi-language UI & accessibility improvements**
- **Autoscaling & production-grade CI/CD pipelines**

---

## Troubleshooting

- **404 on /api requests from frontend?**  
Make sure nginx.conf proxies `/api/` to `backend:5001` and you have rebuilt the image.
- **API failures (OneMap, translation)?**
- Check `.env` and make sure keys are set and valid.
- **Pod/service not running?**  
Use `kubectl logs <pod>` and `kubectl describe pod <pod>` for errors.

---

## File Structure Example:
>```
> /
> ├── backend/
> |   ├── Dockerfile
> |   ├──.env
> |   ├──...
> ├── frontend/
> |   ├── Dockerfile
> |   ├──nginx.conf
> |   └──...
> ├── translation-service/
> |   ├── Dockerfile
> |   ├── requirements.txt
> |   ├──.env
> |   └──...
> ├── docker-compose.yml
> ├── k8s/
> │   ├── backend-deployment.yaml
> │   ├── backend-service.yaml
> │   ├── frontend-deployment.yaml
> │   ├── frontend-service.yaml
> │   ├── translation-deployment.yaml
> │   ├── translation-service.yaml
> │   └── ...
> └── README.md
> ```

---

## Contributing

This is a small project and welcome to feedback.

---

*For more information on each component, see the corresponding README in each subfolder.*

----

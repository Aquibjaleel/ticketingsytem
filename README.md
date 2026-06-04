**CI/CD Architecture**

This repository contains the **Infrastructure-as-Code (IaC)**, **Azure landing zone**, **Kubernetes platform**, and **end‑to‑end DevOps pipelines** for the **Ticketing Application**.

The project now supports **two workflows**:

1.  **Modern CI/CD pipeline workflow** (recommended)
2.  **Local Terraform workflow** (legacy but still supported)

Both are documented below.

***

# 🏗️ High‑Level Architecture

The platform is built on a **secure Azure landing zone** with a **hub–spoke topology**, private networking, and a fully automated AKS deployment.

### **Hub Network**

*   Central VNet (10.0.0.0/16)
*   Subnets:
    *   Application Gateway / WAF
    *   Azure Firewall
    *   Management
*   Shared services: routing, DNS, firewall policies

### **Spoke Network**

*   AKS node subnet
*   Private Endpoints for:
    *   ACR
    *   MySQL Flexible Server
*   Monitoring subnet

### **Application Gateway (WAF\_v2)**

*   Secured public ingress
*   Routes traffic to AKS ingress

### **Azure Firewall**

*   All outbound restricted
*   Explicit allow‑list for:
    *   Azure services
    *   Ubuntu repositories
    *   Monitoring endpoints

### **AKS (Private Cluster)**

*   Azure CNI
*   Private API server
*   ACR integration
*   Firewall‑controlled egress

### **MySQL Flexible Server**

*   Private endpoint only
*   Private DNS zone

***

# ⚙️ DevOps Workflow

The DevOps system now uses **two Azure DevOps YAML pipelines**, both running on the **same local self‑hosted agent**:

***

# 🚀 **1. Infrastructure Pipeline (Terraform)**

📄 File:

    Infra-pipeline/azure-pipelines.yml

### Pipeline Stages:

1.  **Validate** — fmt + validation + backend bootstrap
2.  **Plan** — generates a secure, published Terraform plan
3.  **Apply** — gated deployment to Azure (`environment: dev`)

### Triggers:

*   Manual (for now)
*   Branch: `Infra_and_App_Pipelines`
*   Can be enabled for CI/PR in the future

### Outputs:

*   AKS cluster
*   ACR
*   Hub–Spoke networking
*   Private endpoints
*   Key Vault
*   Firewall + App Gateway

***

# 🚀 **2. Application Pipeline (Docker + AKS Deployment)**

📄 File:

    App-pipeline/azure-pipelines-app.yml

### Pipeline Stages:

1.  **Build**
    *   SonarQube scan
    *   Python testing + coverage
    *   Docker build & push to ACR
2.  **Deploy\_Dev** — deploy manifest to AKS (dev)
3.  **Deploy\_Test** — deploy manifest to AKS (test)
4.  **Deploy\_Prod** — deploy manifest to AKS (prod)

All stages use the **same self‑hosted agent** as the infra pipeline:

    pool:
      name: 'Infra-and-App-Pipeline-AnisLocalAgent'

***

# 🔗 **Automatic Pipeline Chaining**

The **application pipeline starts automatically** after the **infrastructure pipeline succeeds**.

This is enabled using:

```yaml
resources:
  pipelines:
    - pipeline: infraPipeline
      source: <YOUR INFRA PIPELINE NAME>
      trigger: true
```

This ensures:

    Terraform Infrastructure → Application Build → AKS Deployments

No manual intervention required.

***

# 📂 Repository Structure

    /
    ├── Infra-pipeline/
    │   ├── azure-pipelines.yml             # Terraform validate/plan/apply
    │   └── azure-pipelines-destroy.yml
    │
    ├── App-pipeline/
    │   ├── azure-pipelines-app.yml         # App Build + AKS Deploy pipeline
    │   └── env/
    │       ├── dev/
    │       │   ├── deployment.yml
    │       │   └── service.yaml
    │       ├── test/
    │       │   ├── deployment.yml
    │       │   └── service.yaml
    │       └── prod/
    │           ├── deployment.yml
    │           └── service.yaml
    │
    ├── modules/                            # Terraform modules (AKS, ACR, WAF, FW...)
    ├── env/                                # Terraform environments
    │   ├── dev/
    │   ├── test/
    │   └── prod/
    │
    ├── application/                        # Python Flask app source code
    ├── Dockerfile
    ├── requirements.txt
    └── README.md

***

# ⚙️ Legacy Terraform Workflow (Still Supported)

You can still deploy the full environment locally:

### **Set variables**

```bash
export TF_VAR_subscription_id="xxxx"
export TF_VAR_resource_group_name="my-rg"
export TF_VAR_location="canadacentral"
```

### **Plan**

```bash
cd env/dev
terraform init
terraform plan
```

### **Apply**

```bash
terraform apply
```

### **Destroy**

```bash
terraform destroy
```

> ⚠️ Only use the **local workflow** for testing, debugging, and module updates.  
> Production deployments **must** go through CI/CD.

***

# 🔐 Security Baseline

| Component  | Controls                                       |
| ---------- | ---------------------------------------------- |
| Ingress    | App Gateway WAF\_v2 only                       |
| Egress     | Azure Firewall forced tunneling                |
| Secrets    | Azure Key Vault w/ soft delete + purge protect |
| Networking | Private endpoints, no public services          |
| Identity   | Managed Identity for AKS & ACR                 |

***

# 📡 Firewall Rule Summary

### Network Rules (L3/L4)

*   AKS → MySQL PE (3306)
*   AKS → Azure Monitor (443)
*   Outbound HTTPS (443)

### App Rules (L7)

*   AKS → mcr.microsoft.com
*   AKS → Azure API endpoints
*   AKS → Ubuntu package mirrors

Everything else = **blocked**.

***

# 🧪 Monitoring Roadmap (Sprints 2–3)

| Tool          | Purpose                 |
| ------------- | ----------------------- |
| Azure Monitor | Infra metrics + logs    |
| Prometheus    | Pod-level metrics       |
| Grafana       | Dashboards              |
| Alerts        | Error/latency detection |

***

# 📋 Risks & Mitigations

| Risk               | Mitigation                                 |
| ------------------ | ------------------------------------------ |
| Firewall misconfig | Diagrams, peer review, incremental rollout |
| Secret lifecycle   | KV automation, rotation policies           |
| AKS complexity     | IaC modules and repeatable envs            |


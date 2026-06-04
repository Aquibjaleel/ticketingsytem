# Ticketing App Cluster Setup Documentation
---
*An overview of the cluster setup, access, infrastructure, deployment process, Azure Key Vault usage, and maintenance practices.*

## 1. Overview

+ **Cluster Name:** aks-dev
+ **Environment:** Dev
+ **Cloud Provider:** Azure
+ **Purpose of the Cluster:** To provide a secure, isolated, and scalable environment for running the ticketing application inside containerized workloads.
+ **Architecture Summary:** A Kubernetes foundation is provided that is controlled, secure, and easily reproducible for the ticketing application. This ensures the application runs safely inside isolated containers. It also protects the surrounding environment while supporting future operational scaling and maintenance needs.

---

## 2. Access & Authentication
*An explanation of how users, systems, and tools access the cluster.*

### 2.1 Access Requirements 

+ **Required Accounts:**
    + Azure AD user accounts for engineers who need kubectl access.
    + The AKS cluster uses a system‑assigned managed identity (created automatically by Azure).
+ **RBAC Roles:**
    + The cluster’s Kubelet identity is automatically given the AcrPull role on the ACR (azurerm_role_assignment.acr_attach).
+ **Onboarding Steps for New Users:**
    1. User logs in with Azure CLI (az login).
    2. User retrieves AKS credentials.
    3. User can then run kubectl based on their Azure AD permissions.

### 2.2 Authentication Methods

+ **Azure AD Login:**
    + Users authenticate using Azure CLI with their Azure AD account.
    ```
    az login
    ```
    or 
    ```
    az login --use-device-code
    ```
+ **Kubectl Authentication:**    
    + Users obtain cluster credentials with:
    ```
    az aks get-credentials -g <resource_group> -n <cluster_name>
    ```

+ **Tools Used:**
    + Azure CLI - required for login and credential retrieval.
    + Kubectl - command-line tool to interact with the cluster.
    + Microsoft auth plugin - used for Azure AD authentication with kubectl.
    + Pluralsight Azure Sandbox - used for learning and testing cluster access.

### 2.3 Access Restrictions

+ **Network Restrictions:**
    + AKS nodes are deployed into a specific Virtual Network subnets.
    + Pods and nodes receive IPs from these subnets.
  <br>
    + **Hub/Spoke VNets:**

        + **Hub-vnet:** 10.0.0.0/16 with dedicated subnets:
            + AppGatewaySubnet (10.0.0.0/27)
            + AzureFirewallSubnet (10.0.0.64/26)
            + AzureFirewallManagementSubnet (10.0.0.128/26)
            + ManagementSubnet (10.0.1.0/25)

        + **Spoke-vnet:** 10.1.0.0/16 with subnets:

            + AKSNodeSubnet (10.1.0.0/20)
            + MySQL_PESubnet (10.1.32.0/27)
            + ACR_PESubnet (10.1.33.0/27)
            + MonitoringSubnet (10.1.40.0/27)
<br>
    + VNet Peering is established between Hub-vnet and Spoke-vnet.
    + AKS nodes are placed in AKSNodeSubnet and use Azure CNI (pods/nodes get IPs from the VNet).
    + NAT Gateway is enabled on the AKSNodeSubnet in the Spoke (egress via NAT).
    + NSGs are not created by the hub or spoke modules (create_nsgs = false).
    <br>
    + **Private endpoints:**
        + A private endpoint subnet for MySQL is defined and used by the MySQL module (MySQL_PESubnet).
        + A private endpoint subnet for ACR is defined (ACR_PESubnet), but no ACR private endpoint is created in this code.
        + MySQL currently has public_network_access_enabled = true.
    <br>
    + **Application Gateway / WAF:**
        + An Application Gateway (WAF_v2) is deployed in the Hub using a public IP and the dedicated AppGatewaySubnet.
        + WAF mode is set to Detection.

+ **Firewall Rules:**
    + Azure Firewall is deployed in the Hub using AzureFirewallSubnet with a separate management subnet.
    + The firewall module is provided the Spoke address space (10.1.0.0/16) and the MySQL private endpoint IP
---

## 3. Cluster Infrastructure Details
*A list of resources contained inside the cluster, including node pools, networking, and monitoring setup.*

### 3.1 Node Pools

+ **Pool Configuration:**
    + The cluster has one node pool named "default".
    + Node size: Standard_DS2_v2 (set by vm_size = var.vm_size).
    + Node count: 1 node (node_count = var.node_count).
   
+ **Linux Pools:**
    + The node pool is a Linux node pool (default behavior when no Windows settings are provided).
  
+ **SystemNode Pools:**
    + The "default" pool is the system node pool (default behavior when only one pool is defined).

### 3.2 Networking

+ **VNet/Subnet architecture:**
    + The AKS cluster is deployed into the Spoke VNet (10.1.0.0/16).
    + AKS nodes are placed specifically in the AKSNodeSubnet(10.1.0.0/20).
    + The Hub and Spoke VNets are peered using the vnet_peering module.
    + Pods and nodes receive IP addresses from the Spoke VNet.
  
+ **Load Balancers:**
    + The AKS cluster uses the default Azure Load Balancer created automatically by AKS.
  
+ **DNS Usage:**
    + DNS settings for MySQL private endpoint come from the MySQL module.

---

## 4. Deployment Process
*An explanation of how applications are deployed to the cluster, including CI/CD tools, deployment methods, and environment structure.*

### 4.1 Deployment Methods

+ **CI/CD Pipeline Tool:**
    + GitHub is used for CI/D deployment workflows.

### 4.2 Deployment Workflow

+ **Step-by-step deployment flow:**
    + A developer pushes code to the GitHub repository.
    + GitHub Actions runs the CI workflow to build and test the application.
    + The CI workflow builds a container image and pushes it to the Azure Container Registry (ACR) associated with the cluster.
---

## 5. Azure Key Vault (AKV) Usage
*Overview of how the cluster interacts with Azure Key Vault.*

### 5.1 Purpose

+ The Key Vault is used to store secrets required by applications or resources in the environment.
+ The AKS kubelet identity is granted least‑privilege secret access (Get, List) so AKS workloads can read secrets when needed.
+ The current user receives full administrative permissions over secrets, keys, certificates, and storage.

### 5.2 Secret Access Method

+ **Managed Identity:**
    + The AKS cluster uses a system‑assigned managed identity, and its kubelet identity is passed into the AKV module (aks_identity_object_id).
    + That identity is given limited Key Vault access to read secrets only.
+ **Access Policies:**
    + Access policy for current user: Full permissions over keys, secrets, certificates, and storage.

---

## 6. Maintenance & Operations
*Information on how the cluster is maintained, updated, and troubleshooted.*

### 6.1 Backup & Recovery

+ **etcd backups (if self-managed):**
    + The cluster uses Azure-managed control plane, so etcd is managed by Azure. Azure automatically handles etcd backups and recovery for managed AKS clusters. 

### 6.3 Troubleshooting

+ **Common issues**
    + **Permission issues with the Pluralsight Azure Sandbox (e.g., "You do not have permissions to perform this action").**
        + **Solution:** Ensure the user is logged in with the correct Azure AD account that has access to the sandbox environment. Use `az login` to authenticate and `az account show` to verify the current subscription and account details.
  <br>
    + **Authentication issues when trying to access the cluster with kubectl.**
      + **Solution:** Ensure the user has run `az aks get-credentials` to retrieve the cluster credentials and that they are authenticated with Azure AD. Check for any errors during credential retrieval and ensure the correct subscription is set.
  <br>
    + **Network connectivity issues between the cluster and other resources (e.g., ACR, MySQL).**
        + **Solution:** Verify the VNet peering and subnet configurations. Ensure that the AKS nodes have proper network access to the required resources and that NSGs or firewall rules are not blocking traffic. 
  <br>
    + **Resource provisioning failures during cluster creation or scaling.**
        + **Solution:** Check the Azure portal for any failed resource deployments and review the error messages. Ensure that the necessary permissions are in place for resource creation and that there are no quota limits being hit. 
<br>
  
+ **Commands used for diagnosis:**
    + `az aks get-credentials` - to retrieve cluster credentials.
    + `kubectl get nodes` - to check node status and connectivity.
    + `kubectl get pods --all-namespaces` - to check the status of all pods in the cluster.
    + `az login` - to ensure the user is authenticated with Azure.
    + `az account show` - to check the current Azure subscription and account details.
    + `az aks show` - to check the status and details of the AKS cluster.
    + `az aks nodepool list` - to check the status of node pools in the cluster.
    + `az aks nodepool show` - to check details of a specific node pool.
    + `az account set --subscription <subscription_id>` - to switch to the correct Azure subscription if needed.


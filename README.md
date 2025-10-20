# Project Implementation CookBook

## Architecture Diagram

![Architecture Diagram](images/architecture_diagram.png)

# Table of Contents

- [Prerequisites](#prerequisites)
- [Basic Setup & Configuration](#1-basic-setup--configuration)
    - [GitLab Project Repository Initialization](#1a-gitlab-project-repository-initialization)
    - [SonarCloud Security Scanning Setup](#1b-sonarcloud-security-scanning-setup)
- [Google Cloud Storage Configuration for Security Logs](#2-google-cloud-storage-configuration-for-security-logs)
    - [Google Cloud Setup](#2a-google-cloud-setup)
    - [GitLab CI/CD Pipeline](#2b-gitlab-cicd-pipeline-gitlab-ciyml)
- [Setting up Cloud Functions (Log Processing)](#3-setting-up-cloud-functions-log-processing)
    - [Python Function (main.py)](#python-function-mainpy)
- [Google Cloud BigQuery Setup for Data Analysis](#4-google-cloud-bigquery-setup-for-data-analysis)
- [Final Verification and Pipeline Execution](#5-final-verification-and-pipeline-execution)
- [Acknowledgements](#acknowledgements)

## A Step-by-Step Guide for Implementation of a Cloud Computing Security Pipeline
## Prerequisites
> **Note:** This guide aims to cover all major steps for setting up the security pipeline, but some steps may require adaptation or debugging based on your environment. If you find any missing steps or improvements, please feel free to update the process and contribute back!

| Requirement                | Details                                                                 |
|----------------------------|------------------------------------------------------------------------|
| GitLab Account             | Access to create projects and configure CI/CD pipelines                  |
| SonarCloud Account         | Linked to GitLab for SAST integration                                   |
| Google Cloud Account       | Permissions to create buckets, service accounts, BigQuery datasets/tables|
| Service Account Roles      | Storage Admin (GCS), BigQuery Data Editor (BigQuery)                    |
| Python 3.12+               | For Cloud Function runtime                                              |
| Functions Framework        | Required in `requirements.txt` for Cloud Functions                      |
| Google Cloud SDK           | For local testing and deployment (optional but recommended)             |
| Project Billing Enabled    | GCP project must have billing enabled                                   |
| IAM Policy Access          | Ability to set bucket/table permissions and audit logging                |
| Basic YAML Knowledge       | For editing `.gitlab-ci.yml`                                            |

This document outlines the procedure for establishing an automated **DevSecOps pipeline** on **GitLab** that integrates static application security testing (SAST) using **SonarCloud** and exports the resulting security logs to a **Google Cloud Platform (GCP)** data warehouse for compliance and analysis.

## 1. Basic Setup & Configuration

This section covers the initialization of the code repository and the integration of the security scanning tool.

### 1.a. GitLab Project Repository Initialization

1.  **Create a GitLab Account:** Navigate to [`https://gitlab.com/`](https://gitlab.com/) and create an account.
2.  **Create a Personal Blank Project:** Go to the dashboard, select "New Project," and then "Create blank project."
    * **Project Name:** `Security Scanning Pipeline`
    * **Visibility:** `Public`
    * **Configuration:** Check "Initialized repository with a README file."
3.  **Create Necessary Files:** Within the project root, create two files:
    * `.gitlab-ci.yml` (For CI/CD pipeline definition)
    * `sonar-project.properties` (For SonarCloud configuration - typically created alongside your code)

### 1.b. SonarCloud Security Scanning Setup

1.  **Log in to SonarCloud:** Go to [`https://sonarcloud.io/`](https://sonarcloud.io/) and log in using your GitLab Account.
2.  **Import Organization:** Click "Analyze new Project," then "Import New Organization," and "Import my personal GitLab group."
3.  **Generate GitLab Personal Access Token:** In your GitLab project, go to **Settings** $\rightarrow$ **Access Token**. Create a new token with the **`api`** scope and securely copy the generated value.
4.  **Connect SonarCloud:** Paste the token into SonarCloud and proceed to map your organization.
    * **Organization Key:** `security-scanning-pipeline`
    * https://gitlab.com/{your-org-name}/security-scanning-pipeline
5.  **Select Project:** Choose the `Security Scanning Pipeline` project and select **"With GitLab CI/CD Pipeline"** to finalize the integration.
6.  **Set Up Quality Gates and Security Rules:** In SonarCloud, configure quality gates and security rules for automated enforcement.
7.  **Configure Notifications:** Set up notifications for failed scans or critical vulnerabilities in SonarCloud.

> (Note: If any issues watch the [YouTube video](https://www.youtube.com/watch?v=3CON6nsTOy0))


## 2. Google Cloud Storage Configuration for Security Logs

This outlines the necessary steps to configure GCP for secure storage of security reports generated by the GitLab CI/CD pipeline.

*(Prerequisites: Active Google Cloud Account)*

### 2.a. Google Cloud Setup

**Step 1: Create a Google Cloud Storage Bucket**
1.  Go to the Google Cloud Console ([`https://console.cloud.google.com/`](https://console.cloud.google.com/)) and click **"Create Bucket."**
2.  Enter a unique name (e.g., `gitlab-security-logs`).
3.  Choose **Standard** storage class, select a location, and set **Access control** to **Uniform**.

**Step 2: Generate a Service Account for GitLab Access**
1.  Navigate to [IAM & Admin](https://console.cloud.google.com/iam-admin/serviceaccounts) $\rightarrow$ Service Accounts.
2.  Click **"Create Service Account."** Enter a name (e.g., `gitlab-storage-service`).
3.  Assign the following roles to the service account:
    - **Storage Admin** (for GCS buckets)
    - **BigQuery Data Editor** (for BigQuery dataset/table access)
4.  Find the new service account, click **"Manage keys,"** then **"Add Key"** $\rightarrow$ **"Create new key."** Select **JSON** format and download the file.

```
{
  "type": "service_account",
  "project_id": "********",
  "private_key_id": "********",
  "private_key": "-----BEGIN PRIVATE KEY-----\n********\n-----END PRIVATE KEY-----\n",
  "client_email": "********@********.iam.gserviceaccount.com",
  "client_id": "********",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/********@********.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```


**Step 3: Add Google Cloud Credentials to GitLab**
1.  In your GitLab project, go to **Settings** $\rightarrow$ **CI/CD** $\rightarrow$ **Variables**.
2.  Click "Add Variable" and create the following:
    * **Key:** `GOOGLE_APPLICATION_CREDENTIALS`
    * **Value:** Paste the entire JSON content from the downloaded service account key file.

**Step 4: Network and Security Best Practices**
1. Restrict access to GCS buckets using IAM policies.
2. Enable audit logging for GCS and BigQuery for compliance tracking.

![image1](/images/image1.png)

### 2.b. GitLab CI/CD Pipeline (`.gitlab-ci.yml`)

This pipeline defines the automated process of code retrieval, SonarQube scanning, and log export to GCS.

- [.gitlab-ci.yml code](.gitlab-ci.yml)

## 3. Setting up Cloud Functions (Log Processing)

A Google Cloud Function is deployed to trigger automatically upon log file upload to the GCS bucket. This function parses the JSON, uploads the extracted data to **BigQuery**, and generates a clean CSV file.

**Steps for Cloud Function Deployment:**

1.  **Create Function:** In the Google Cloud Console, navigate to Cloud Functions and click **"Create Function."**
2.  **Basic Settings:** Provide a Function name, select a Region, and set the **Runtime** to **Python 3.12**.
3.  **Source Code:** Select the **Inline Editor** option and use the following code for the main function and dependencies.

![image2](/images/image2.png)

4.  **Trigger Configuration:**
    * **Trigger Type:** **Cloud Storage**
    * **Event Type:** **Finalize/Create** (Trigger when a new file is uploaded)
    * **Bucket:** Specify the GCS bucket name (`gitlab-security-logs`).
5.  **Entry Point:** Enter the function name: `hello_gcs`.
6.  Click **Deploy**.

### Python Function (`main.py`)

The core logic for processing security logs and exporting to BigQuery is implemented in the following Python file:

- [`main.py`](main.py)

**Dependencies (`requirements.txt`):**

```text
functions-framework==3.*
google-cloud-storage>=2.0.0
google-cloud-bigquery>=3.0.0
```



## 4. Google Cloud BigQuery Setup for Data Analysis

> **Note:** The BigQuery resources must be created before the Cloud Function executes to successfully receive and store data.

### 4.a. Create BigQuery Dataset

1. Go to the [BigQuery Console](https://console.cloud.google.com/bigquery).
2. Click the three dots next to your project ID and select **Create dataset**.
3. **Dataset ID:** `security_scans`
4. Set the Data location and click **Create dataset**.

### 4.b. Create BigQuery Table

1. Click the newly created `security_scans` dataset.
2. Click **CREATE TABLE**.
3. **Source:** Select **Empty table**.
4. **Table name:** `issues_data`
5. **Schema Definition (Recommended):** While the Cloud Function uses `autodetect=True`, defining the core schema fields is good practice:

| Field Name         | Data Type | Mode     | Description                                      |
|--------------------|-----------|----------|--------------------------------------------------|
| key                | STRING    | NULLABLE | Unique issue identifier                          |
| rule               | STRING    | NULLABLE | The security rule violated                       |
| severity           | STRING    | NULLABLE | Severity level (e.g., CRITICAL, MAJOR)           |
| component          | STRING    | NULLABLE | File path                                        |
| line               | INTEGER   | NULLABLE | Line number                                      |
| file_upload_time   | TIMESTAMP | NULLABLE | Timestamp of GCS upload (metadata)               |
| source_file        | STRING    | NULLABLE | Name of the source JSON file (metadata)          |

6. Click **Create table**.



## 5. Pipeline Execution

### 5.a. Update Project Placeholders

Ensure the following placeholders in your `.gitlab-ci.yml` and Python function are updated with your actual resource names:

| Placeholder | Location | Description |
|-------------|----------|-------------|
| `neelkanth-khithani_security-scanning-pipeline` | `.gitlab-ci.yml` (Sonar Scanner) | Your SonarCloud Project Key |
| `672844091200` | `.gitlab-ci.yml` (`gcloud config set project`) | Your Google Cloud Project Number |
| `gs://your-json-uploads/` | `.gitlab-ci.yml` (`gsutil cp`) | Your Source GCS Bucket Name (e.g., `gitlab-security-logs`) |
| `your-processed-csvs` | Python Function (`output_bucket` variable) | Your Destination GCS Bucket Name for CSV files |

### 5.b. Create a sample test vulnerable GitHub Repository

- A GitHub repository containing deliberately vulnerable code (e.g., vulnerable-testapp) is created and populated with source files that are known to fail security checks.

![Test Repo Image](/images/test_repo.png)

Pushing it to GitHub

![Project commiting to github](/images/project_commit.png)

![Github_vulnerable_app_repo](/images/Github_vulnerable_app_repo.png)


### 5.c. Commit and Run the Pipeline

> Ensure Cloud Resource Manager API is Enabled: Visit the link and enable it.
https://console.cloud.google.com/apis/api/cloudresourcemanager.googleapis.com 

After finalizing all configurations and updates:

1. **Commit Changes:** Commit the completed `.gitlab-ci.yml` to your GitLab repository.
2. **Trigger:** The commit will automatically trigger the CI/CD pipeline. Monitor the pipeline status in the **GitLab CI/CD → Pipelines** section.

![Pipeline Executing on GitLab](images/gitlab_pipeline_exectued.png)

### 5.c. Verify Results

- **Google Cloud Storage (Source Bucket):** Verify that the security report JSON file (e.g., `sonarqube_report.json`) has been successfully uploaded by the `export_logs` job.

![sonarqube_report.json](images/your-json-uploads.png)

- **Google Cloud Storage (Destination Bucket):** Verify the automatic creation of a `processed/` folder containing the resulting CSV file (e.g., `processed/sonarqube_report.csv`).

![sonarqube_report.csv](images/your-processed-csvs.png)

- **Google Cloud BigQuery:** In the BigQuery console, check the `security_scans.issues_data` table. The number of rows should reflect the number of security issues found, confirming a successful end-to-end data load.

![security_scans.issues_data](images/issues_data.png)


### 5.d. Gemini Model Integration and Vulnerable Code Fix

To maximize the practical value of the security pipeline, the final CSV output containing the vulnerability data is integrated into a user-facing web application. This application serves two critical functions:

- **Visibility**: It displays the raw security findings (imported from BigQuery/CSV), making the list of vulnerabilities accessible and understandable to developers.

- **Guided Remediation**: The application is powered by the Gemini model through an integrated chat interface. Developers can select a specific vulnerability from the list and use the chat to ask the Gemini model for detailed explanations, remediation steps, and concrete code examples to fix the error.

![App](/images/app.png)




# Acknowledgements

This project was developed as part of the Cloud Computing under the Computer Engineering Department, V.E.S. Institute of Technology, Mumbai.

## Contributors

| Role | Name | Contact |
| :--- | :--- | :--- |
| **Project Implementer** | Neelkanth Khithani | 2022.neelkanth.khithani@ves.ac.in |
| **Project Implementer** | Ishwari Dehadray | 2022.ishwari.dehadray@ves.ac.in |
| **Project Implementer** | Atharv Inamdar | 2022.atharv.inamdar@ves.ac.in |
| **Project Mentor** | Mr. Richard Joseph | richard.joseph@ves.ac.in |

I would like to express my sincere gratitude to Mr. Richard Joseph, Professor, Computer Engineering Department, for her invaluable guidance, encouragement, and support throughout this project.
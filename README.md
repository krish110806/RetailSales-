# RetailPulse

### Retail Sales Analytics & Automated Data Pipeline

RetailPulse is a retail sales analytics project that brings data
ingestion, data quality checks, transformation, pipeline monitoring, and
business reporting into one application. It uses the Sample Superstore
dataset to help explore sales, profit, product performance, and regional
trends.

> **Project type:** Data Engineering / Data Analytics Microproject\
> **Primary interface:** Streamlit\
> **Dataset:** Sample Superstore retail sales data

------------------------------------------------------------------------

## Table of Contents

-   [Project Overview](#project-overview)
-   [Objectives](#objectives)
-   [Key Features](#key-features)
-   [Technology Stack](#technology-stack)
-   [System Architecture](#system-architecture)
-   [Project Structure](#project-structure)
-   [Dataset](#dataset)
-   [Getting Started](#getting-started)
-   [Running the Application](#running-the-application)
-   [Pipeline and Data Flow](#pipeline-and-data-flow)
-   [dbt Models](#dbt-models)
-   [Airflow Orchestration](#airflow-orchestration)
-   [Airbyte Configuration](#airbyte-configuration)
-   [Ask Your Data](#ask-your-data)
-   [Configuration and Security](#configuration-and-security)
-   [Testing](#testing)
-   [Current Implementation Notes](#current-implementation-notes)
-   [Future Enhancements](#future-enhancements)

------------------------------------------------------------------------

## Project Overview

Retail businesses generate transaction data that can be used to
understand revenue, profitability, product demand, and regional
performance. However, raw data often needs to be inspected, cleaned,
validated, transformed, and organized before it can support reliable
analysis.

RetailPulse demonstrates this workflow through a structured data
pipeline and an interactive dashboard. The project includes data
preparation and validation modules, storage for pipeline outputs and run
information, dbt SQL models, an Airflow DAG, an Airbyte configuration
template, and a six-page Streamlit interface.

The application is designed to make both the data engineering workflow
and the resulting business insights easier to inspect.

## Objectives

-   Ingest retail sales records from CSV data.
-   Profile and validate incoming records.
-   Separate accepted records from rejected records and record rejection
    reasons.
-   Store cleaned data and data quality reports.
-   Transform sales data into analytical models using dbt.
-   Define pipeline task dependencies through Apache Airflow.
-   Present sales and operational metrics through Streamlit.
-   Support common business questions through the Ask Your Data page.

## Key Features

### 1. Sales Overview

A summary of key retail performance indicators, with a high-level view
of sales and profit.

### 2. Sales Analytics

Explore sales performance over time and compare relevant sales measures.

### 3. Product Analytics

Review product and category performance to identify high-performing
products.

### 4. Regional Analytics

Compare sales and profitability across geographic regions.

### 5. Ask Your Data

Use the conversational-style query interface to explore supported
business questions, such as: - Which product has the highest revenue? -
Which region has the highest sales? - How do sales change month by
month? - Which category generates the highest profit?

The answers should be interpreted from the application's available data
and query logic.

### 6. Data Pipeline

Inspect pipeline activity and data quality information, including input,
cleaned and rejected records, validation results, and run information
where available.

------------------------------------------------------------------------

## Technology Stack

  Technology       Purpose
  ---------------- ---------------------------------------------------
  Python           Pipeline and application logic
  Pandas           Data preparation and analysis
  Streamlit        Interactive dashboard
  Plotly           Data visualizations
  Apache Airflow   Workflow orchestration
  Airbyte          Configurable data ingestion connector
  dbt              SQL-based data transformation and testing
  BigQuery         Cloud data warehouse target
  SQLite           Local persistence for supported pipeline metadata
  SQL              Analytical transformations and queries

The project contains configuration for these components. Actual cloud
execution requires the relevant services, packages, credentials, and
connector setup to be configured in the deployment environment.

------------------------------------------------------------------------

## System Architecture

``` mermaid
flowchart TD
    A["Sample Superstore CSV"] --> B["Ingestion"]
    B --> C["Raw Data"]
    C --> D["Profiling and Validation"]
    D -->|Valid records| E["Cleaned Data"]
    D -->|Invalid records| F["Rejected Records"]
    D --> G["Data Quality Reports"]
    E --> H["dbt Staging Model"]
    H --> I["dbt Analytical Models"]
    I --> J["Analytics Data"]
    B -. "Configured connector" .-> K["Airbyte"]
    K -. "Configured destination" .-> C
    L["Apache Airflow DAG"] -. "Orchestrates tasks" .-> B
    L -.-> H
    J --> M["Streamlit Dashboard"]
    E --> M
    F --> M
    G --> M
```

**Architecture summary:** CSV data enters the ingestion workflow, then
passes through profiling and validation. Accepted and rejected records
are stored separately, while quality reports capture validation results.
dbt models provide analytical tables, Airflow defines task
orchestration, and Streamlit presents business and pipeline information.

------------------------------------------------------------------------

## Project Structure

``` text
Retail Pulse/
│
├── .streamlit/
│   └── config.toml
│
├── airflow/
│   └── dags/
│       └── retailpulse_etl_pipeline.py
│
├── dashboard/
│   ├── pages/
│   │   ├── page_1_sales_overview.py
│   │   ├── page_2_sales_analytics.py
│   │   ├── page_3_product_analytics.py
│   │   ├── page_4_regional_analytics.py
│   │   ├── page_5_ask_your_data.py
│   │   └── page_6_data_pipeline.py
│   └── utils/
│       ├── bi_query_engine.py
│       └── theme.py
│
├── data/
│   ├── raw/
│   │   ├── Sample-Superstore.csv
│   │   └── superstore_sample_1000.csv
│   ├── processed/
│   │   └── latest_cleaned_sales.csv
│   ├── rejected/
│   │   └── latest_rejected_records.csv
│   └── reports/
│       ├── data_profiling_report.json
│       ├── data_profiling_report.md
│       └── latest_quality_report.json
│
├── dbt_retailpulse/
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_retail_sales.sql
│   │   └── marts/
│   │       ├── fct_sales.sql
│   │       ├── monthly_sales.sql
│   │       ├── product_performance.sql
│   │       └── regional_sales.sql
│   ├── tests/
│   ├── dbt_project.yml
│   └── profiles.yml.example
│
├── ingestion/
│   └── airbyte_config.json
│
├── pipeline/
│   ├── bigquery_client.py
│   ├── cleaner_validator.py
│   ├── db_manager.py
│   ├── dbt_runner.py
│   ├── ingestion.py
│   └── pipeline_engine.py
│
├── scripts/
│   └── profile_and_sample.py
│
├── tests/
│   └── test_pipeline.py
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
└── docker-compose.yml
```

------------------------------------------------------------------------

## Dataset

RetailPulse uses the **Sample Superstore** dataset, a sample retail
transactions dataset commonly used for sales analysis.

The project includes: - `Sample-Superstore.csv` --- source dataset. -
`superstore_sample_1000.csv` --- a representative sample used by the
project.

Common fields include:

  Field                    Description
  ------------------------ ----------------------------
  Order ID                 Identifier for the order
  Order Date               Date the order was placed
  Ship Date                Date the order was shipped
  Ship Mode                Shipping method
  Customer ID              Customer identifier
  Segment                  Customer segment
  City, State, Region      Geographic information
  Product ID               Product identifier
  Category, Sub-Category   Product classification
  Product Name             Product description
  Sales                    Recorded sales amount
  Quantity                 Units sold
  Discount                 Discount applied
  Profit                   Recorded profit amount

**Data note:** The `Sales` column is treated as the recorded sales
amount in the source data. It should not be multiplied by `Quantity`
again when calculating revenue.

------------------------------------------------------------------------

## Getting Started

### Prerequisites

Install the following before running the project:

-   Python 3.10 or a compatible version supported by the dependencies.
-   pip.
-   Git (optional, for cloning the repository).
-   Access to the relevant cloud services only if using the cloud
    warehouse or external connectors.

### 1. Clone the repository

``` bash
git clone https://github.com/krish110806/RetailSales-.git
cd RetailSales-
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using the example:

**Windows PowerShell**

``` powershell
Copy-Item .env.example .env
```

Open `.env` and fill in only the settings needed for your chosen
execution mode. Do not commit real credentials.

### 5. Configure dbt (if running dbt)

Create a local `profiles.yml` from the example file:

``` powershell
Copy-Item dbt_retailpulse/profiles.yml.example dbt_retailpulse/profiles.yml
```

Edit the profile for the warehouse you have configured. Set the
appropriate environment variables and authentication details locally.
The actual `profiles.yml` is intentionally excluded from version
control.

------------------------------------------------------------------------

## Running the Application

From the project root, activate the virtual environment and run:

``` bash
streamlit run app.py
```

Streamlit will print a local URL in the terminal, usually:

``` text
http://localhost:8501
```

Open the displayed URL in your browser.

------------------------------------------------------------------------

## Pipeline and Data Flow

The pipeline is organized into the following logical stages:

1.  **Source:** Read the supplied retail CSV dataset.
2.  **Ingestion:** Load the source records into the pipeline workflow.
3.  **Profiling:** Inspect columns, data types, missing values, and
    duplicate records.
4.  **Validation:** Apply the project's data quality rules.
5.  **Separation:** Store accepted records in the processed output and
    invalid records in the rejected output, with reasons where
    available.
6.  **Reporting:** Generate data profiling and quality reports.
7.  **Transformation:** Build staging and analytical models using dbt
    when configured.
8.  **Orchestration:** Use the Airflow DAG to define task order and
    dependencies.
9.  **Visualization:** Explore business and pipeline information in
    Streamlit.

The exact stages executed depend on the selected local or cloud
configuration. A configuration file or DAG definition alone does not
mean an external Airbyte, BigQuery, or Airflow service has been
connected and successfully run.

------------------------------------------------------------------------

## dbt Models

The dbt project contains a staging model and analytical models:

  Model                   Purpose
  ----------------------- -------------------------------------------------
  `stg_retail_sales`      Staging and preparation of retail sales records
  `fct_sales`             Sales fact model
  `monthly_sales`         Monthly sales analysis
  `product_performance`   Product performance analysis
  `regional_sales`        Regional sales analysis

Custom SQL tests are included for positive quantity and positive sales
checks. Run dbt commands from the dbt project directory after
configuring the profile and warehouse:

``` bash
cd dbt_retailpulse
dbt debug
dbt run
dbt test
```

These commands require a working dbt adapter, profile, credentials, and
accessible source relations.

------------------------------------------------------------------------

## Airflow Orchestration

The project includes the DAG:

``` text
airflow/dags/retailpulse_etl_pipeline.py
```

It defines the workflow and dependencies for the retail sales pipeline.
To execute it through Apache Airflow, install and configure Airflow in a
compatible environment, place the DAG in the configured DAG directory,
and configure the required connections and variables.

A DAG file in the repository is the workflow definition; a successful
Airflow run must be verified in the Airflow environment.

------------------------------------------------------------------------

## Airbyte Configuration

The project includes an Airbyte configuration template:

``` text
ingestion/airbyte_config.json
```

It documents the intended CSV source and warehouse destination
configuration. Configure the source, destination, credentials, and
accessible file location in your Airbyte deployment before running a
sync. Environment-variable placeholders in the template must be supplied
by the deployment or setup process; they are not credentials by
themselves.

------------------------------------------------------------------------

## Ask Your Data

The Ask Your Data page provides a conversational-style way to explore
supported retail questions. Example questions include:

-   Which product has the highest revenue?
-   Which region has the highest sales?
-   What is the monthly sales trend?
-   Which category has the highest profit?

The query interface uses the project's query logic and available data.
It is not a general-purpose AI assistant unless an AI service is
separately integrated.

------------------------------------------------------------------------

## Configuration and Security

-   Keep `.env` local and never commit it.
-   Keep service-account keys, `credentials.json`, private keys, and
    real warehouse credentials out of Git.
-   Use `.env.example` and `profiles.yml.example` for safe configuration
    templates.
-   Do not place passwords or API keys in source code, screenshots, or
    public documentation.
-   Review `.gitignore` before pushing changes to a public repository.

------------------------------------------------------------------------

## Testing

The repository includes automated tests under:

``` text
tests/
```

Run the available tests from the project root:

``` bash
python -m unittest discover -s tests -v
```

A passing test suite validates only the behaviors covered by those
tests. Separately verify cloud services, Airbyte syncs, dbt execution,
and Airflow runs in their respective environments.

------------------------------------------------------------------------

## Current Implementation Notes

RetailPulse is structured to support local development as well as
integrations with external data engineering tools. The dashboard and
local pipeline workflow can be developed and demonstrated independently
of cloud services.

Before presenting a cloud component as operational, verify the
corresponding live setup: - Airbyte source and destination are
configured and a sync has completed. - BigQuery datasets and tables
exist and can be queried. - dbt models and tests have run successfully
against the configured warehouse. - The Airflow DAG has been loaded and
completed successfully.

This distinction keeps project documentation accurate and makes the
implementation easier to explain during evaluation.

------------------------------------------------------------------------

## Future Enhancements

-   Complete and validate a scheduled Airbyte-to-BigQuery sync.
-   Add incremental ingestion and change detection.
-   Expand dbt schema tests and documentation.
-   Add automated pipeline alerts and retry handling.
-   Add more historical trend and forecasting analysis.
-   Deploy the dashboard and orchestration services to a hosted
    environment.
-   Add role-based access and authentication for dashboard users.

------------------------------------------------------------------------

## Author

**RetailPulse --- Retail Sales Analytics & Automated Data Pipeline**

GitHub: <https://github.com/krish110806/RetailSales->

------------------------------------------------------------------------

*This README describes the repository structure and intended workflow.
Actual execution of external services depends on environment
configuration and successful service setup.*

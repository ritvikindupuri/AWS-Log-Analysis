# AWS CloudTrail Anomaly Detection: Machine Learning with PySpark

## Executive Summary
This project implements an automated threat detection pipeline designed to identify anomalous user behavior and operational irregularities within AWS CloudTrail logs. By leveraging **PySpark** for big data processing and **KMeans Clustering** for unsupervised machine learning, the solution analyzes over **1.9 million log records** to flag potential security breaches, misconfigurations, or policy violations that static rule-based alerts often miss.

The primary objective was to move beyond signature-based detection and utilize statistical deviation to identify "unknown unknowns" in cloud infrastructure usage.

### 🔴 [Launch Interactive Dashboard](https://aws-service-anomaly.manus.space)
*Explore the live anomalies, geographical maps, and service heatmaps hosted on the web.*

## Technical Architecture & Stack
* **Data Processing:** Apache PySpark (Scalable log ingestion and transformation)
* **Machine Learning:** Spark MLlib (KMeans Clustering, Vector Assembly)
* **Visualization:** Plotly ([Live Interactive Dashboard](https://aws-service-anomaly.manus.space) for Security Operations)
* **Data Source:** AWS CloudTrail Logs (~2 million events)

## Methodology: The Machine Learning Pipeline

### 1. Training Data & Feature Engineering
The model was trained on a dataset of **1,939,214 CloudTrail events**, treating the entire historical log as the baseline for "normal" activity.
* **Feature Selection:** I selected high-dimensional features that define the context of an API call: `eventSource` (Service), `awsRegion` (Location), `userIdentitytype` (Actor), and `errorCode` (Outcome).
* **Transformation:** Because machine learning algorithms require numerical input, I built a PySpark pipeline to convert these categorical strings into mathematical vectors using **String Indexing** and **One-Hot Encoding**.

### 2. Algorithm: Unsupervised Anomaly Detection
I utilized **KMeans Clustering (k=10)**, an unsupervised algorithm that groups data points into clusters based on similarity.
* **How it Works:** The model identifies 10 distinct "patterns" of normal usage (clusters) within the 1.9 million events. It does not require labeled "attack" data; instead, it learns what "normal" looks like mathematically.
* **Anomaly Scoring:** For every new event, the model calculates the **Euclidean distance** between that event and the center (centroid) of its nearest cluster.
* **Thresholding:** A threshold of **1.8** was established. Events with a distance score > 1.8 are mathematically distant from any known normal pattern, marking them as anomalies.

## Visual Analysis & Security Insights

### Statistical Anomaly Distribution
To validate the model's thresholding logic, I analyzed the distribution of anomaly scores.

<p align="center">
  <img src=".assets/score_distribution.png" alt="Distribution of Anomaly Scores" width="800"/>
  <br>
  <b>Figure 1: Distribution of Anomaly Scores</b>
</p>

The histogram above visualizes the separation between normal traffic (blue) and flagged anomalies (red). The clear "long tail" distribution confirms that the model successfully isolated rare, high-distance events—indicative of outliers—while clustering the majority of traffic as normal behavior.

### Geographical Risk Mapping
A critical indicator of compromised credentials is API activity originating from unusual geographic locations (impossible travel or geo-hopping).

<p align="center">
  <img src=".assets/choropleth_map.png" alt="Global Distribution of AWS Anomalies" width="800"/>
  <br>
  <b>Figure 2: Global Distribution of AWS Anomalies</b>
</p>

This choropleth map isolates the specific regions generating anomalous traffic. By mapping AWS regions to ISO country codes, the visualization highlights hotspots of irregular activity, allowing security teams to quickly identify if an account is being accessed from a sanctioned or unexpected country.

### Service-Level Threat Vectoring
Understanding *which* services are being targeted is essential for prioritizing incident response.

<p align="center">
  <img src=".assets/top_sources.png" alt="Top 10 AWS Services with Anomalies" width="800"/>
  <br>
  <b>Figure 3: Top 10 AWS Services with Anomalies</b>
</p>

The analysis reveals that **EC2** and **S3** are the primary targets for anomalous activity. This high volume of anomalies in compute and storage services suggests potential data exfiltration attempts (S3) or unauthorized compute provisioning (EC2/Crypto-mining).

### Granular Event Analysis (Heatmap)
To operationalize these findings, I correlated specific API calls (`eventName`) with failure types (`errorCode`).

<p align="center">
  <img src=".assets/Anomaly Heatmap.png" alt="Anomaly Heatmap" width="800"/>
  <br>
  <b>Figure 4: Anomaly Heatmap (Event Name vs. Error Code)</b>
</p>

This heatmap provides the "smoking gun" for investigation:
* **High-Volume Errors:** The density of `Client.InvalidSnapshot.NotFound` combined with `DescribeSnapshots` suggests automated reconnaissance scripts blindly scanning for resources that do not exist.
* **Access Denied Spikes:** The correlation between `ListClusters` and `AccessDenied` indicates a potential privilege escalation attempt where a user is probing for permissions they do not possess.

## MITRE ATT&CK Alignment
The anomalies detected by this model map directly to known adversary tactics:

| Tactic | Technique | Indicator from Model |
| :--- | :--- | :--- |
| **Discovery** | Cloud Service Discovery (T1526) | High frequency of `Describe*` and `List*` API calls flagged in the Heatmap. |
| **Credential Access** | Brute Force (T1110) | Spikes in `AccessDenied` errors across multiple services. |
| **Defense Evasion** | Unused/Unsupported Region (T1535) | Anomalous API calls originating from non-standard AWS regions (Figure 2). |

## Conclusion
This project demonstrates that **machine learning is a viable and necessary layer of defense** for cloud security. By moving beyond static thresholds, the KMeans model successfully identified nuanced attack patterns—such as reconnaissance probing and geographic anomalies—buried within millions of legitimate events. The resulting visualizations provide Security Operations Centers (SOC) with immediate, actionable intelligence to triage threats effectively.

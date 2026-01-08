# AWS CloudTrail Anomaly Detection: Machine Learning with PySpark

## Executive Summary
This project implements an automated threat detection pipeline designed to identify anomalous user behavior and operational irregularities within AWS CloudTrail logs. By leveraging **PySpark** for big data processing and **KMeans Clustering** for unsupervised machine learning, the solution analyzes over **1.9 million log records** to flag potential security breaches, misconfigurations, or policy violations that static rule-based alerts often miss.

The primary objective was to move beyond signature-based detection and utilize statistical deviation to identify "unknown unknowns" in cloud infrastructure usage.

**Interactive Dashboard:** [View the Live Anomaly Analysis](https://aws-service-anomaly.manus.space)

## Technical Architecture & Stack
* **Data Processing:** Apache PySpark (Scalable log ingestion and transformation)
* **Machine Learning:** Spark MLlib (KMeans Clustering, Vector Assembly)
* **Visualization:** Plotly (Interactive dashboards for Security Operations)
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
To validate the model's thresholding logic, I analyzed the distribution of anomaly scores across the entire dataset.

<p align="center">
  <img src=".assets/score_distribution.png" alt="Distribution of Anomaly Scores" width="800"/>
  <br>
  <b>Figure 1: Distribution of Anomaly Scores</b>
</p>

The histogram above validates the effectiveness of the KMeans distance metric. The distribution shows a distinct separation between the majority of "normal" traffic (clustered to the left in blue) and the "anomalous" events (the long tail to the right in red).
* **Analysis:** The events in the red tail possess high Euclidean distance scores (> 1.8), indicating they possess feature combinations (e.g., a specific error code in a rare region) that the model has rarely seen. This statistical separation confirms that the model is not flagging random noise, but is identifying genuine outliers.

### Geographical Risk Mapping
A critical indicator of compromised credentials is API activity originating from unusual geographic locations (impossible travel or geo-hopping).

<p align="center">
  <img src=".assets/choropleth_map.png" alt="Global Distribution of AWS Anomalies" width="800"/>
  <br>
  <b>Figure 2: Global Distribution of AWS Anomalies</b>
</p>

This choropleth map visualizes the physical origin of the anomalous API calls. By mapping AWS region codes to ISO country codes, I was able to isolate hotspots of irregular activity.
* **Analysis:** The concentration of anomalies in specific regions (dark red) suggests a targeted campaign or a misconfigured service operating outside of approved compliance zones. Security teams can use this view to instantly correlate alerts with "Impossible Travel" scenarios, where a single identity appears to initiate API calls from two distant countries simultaneously.

### Service-Level Threat Vectoring
Understanding *which* services are being targeted is essential for prioritizing incident response.

<p align="center">
  <img src=".assets/top_sources.png" alt="Top 10 AWS Services with Anomalies" width="800"/>
  <br>
  <b>Figure 3: Top 10 AWS Services with Anomalies</b>
</p>

This bar chart breaks down the anomalies by AWS Service source. The data reveals a distinct pattern of targeting Compute and Storage infrastructure.
* **Analysis:** The dominance of **EC2** (Elastic Compute Cloud) and **S3** (Simple Storage Service) in the anomaly data is a strong indicator of an attack chain. High anomaly counts in EC2 often correlate with unauthorized instance provisioning (cryptojacking), while anomalies in S3 typically signal data enumeration or exfiltration attempts. This insight allows the SOC to prioritize hardening efforts on these two specific service planes.

### Granular Event Analysis (Heatmap)
To operationalize these findings, I correlated specific API calls (`eventName`) with failure types (`errorCode`).

<p align="center">
  <img src=".assets/Anomaly Heatmap.png" alt="Anomaly Heatmap" width="800"/>
  <br>
  <b>Figure 4: Anomaly Heatmap (Event Name vs. Error Code)</b>
</p>

This heatmap provides the most granular forensic view of the dataset, identifying specific behavioral signatures.
* **Reconnaissance Detected:** The high density of `Client.InvalidSnapshot.NotFound` errors correlating with `DescribeSnapshots` calls (shown in the darker red blocks) is a classic signature of an automated script. The script is likely enumerating snapshot IDs sequentially, failing frequently because the IDs do not exist.
* **Privilege Escalation Probing:** The correlation between `ListClusters` and `AccessDenied` suggests a user identity attempting to access resources it does not have permission to view. This is often an early warning sign of a compromised credential attempting to move laterally or escalate privileges within the account.

## MITRE ATT&CK Alignment
The anomalies detected by this model map directly to known adversary tactics:

| Tactic | Technique | Indicator from Model |
| :--- | :--- | :--- |
| **Discovery** | Cloud Service Discovery (T1526) | High frequency of `Describe*` and `List*` API calls flagged in the Heatmap. |
| **Credential Access** | Brute Force (T1110) | Spikes in `AccessDenied` errors across multiple services. |
| **Defense Evasion** | Unused/Unsupported Region (T1535) | Anomalous API calls originating from non-standard AWS regions (Figure 2). |

## Conclusion
This project demonstrates that **machine learning is a viable and necessary layer of defense** for cloud security. By moving beyond static thresholds, the KMeans model successfully identified nuanced attack patterns—such as reconnaissance probing and geographic anomalies—buried within millions of legitimate events. The resulting visualizations provide Security Operations Centers (SOC) with immediate, actionable intelligence to triage threats effectively.

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Initialize Spark Session
spark = SparkSession.builder.appName("AnomalyVisualizationsFinalRefined").getOrCreate()

# Load results
df_results = spark.read.parquet("/home/ubuntu/anomaly_results.parquet")

# 1. Refined Choropleth Map with Clear Legend
region_stats = df_results.groupBy("awsRegion", "is_anomaly").count().toPandas()
aws_region_to_country = {
    'us-east-1': 'USA', 'us-east-2': 'USA', 'us-west-1': 'USA', 'us-west-2': 'USA',
    'af-south-1': 'ZAF', 'ap-east-1': 'HKG', 'ap-south-1': 'IND', 'ap-northeast-3': 'JPN',
    'ap-northeast-2': 'KOR', 'ap-southeast-1': 'SGP', 'ap-southeast-2': 'AUS',
    'ap-northeast-1': 'JPN', 'ca-central-1': 'CAN', 'eu-central-1': 'DEU',
    'eu-west-1': 'IRL', 'eu-west-2': 'GBR', 'eu-south-1': 'ITA', 'eu-west-3': 'FRA',
    'eu-north-1': 'SWE', 'me-south-1': 'BHR', 'sa-east-1': 'BRA'
}
region_stats['iso_alpha'] = region_stats['awsRegion'].map(aws_region_to_country)
country_stats = region_stats.groupby(['iso_alpha', 'is_anomaly'])['count'].sum().reset_index()
country_pivot = country_stats.pivot(index='iso_alpha', columns='is_anomaly', values='count').fillna(0)
if False not in country_pivot.columns: country_pivot[False] = 0
if True not in country_pivot.columns: country_pivot[True] = 0
country_pivot = country_pivot.rename(columns={False: 'Normal', True: 'Anomaly'})
country_pivot = country_pivot.reset_index()

fig_map = px.choropleth(country_pivot, locations="iso_alpha", color="Anomaly", 
                    hover_name="iso_alpha", hover_data=["Normal", "Anomaly"],
                    title="Global Distribution of AWS Anomalies", 
                    color_continuous_scale=px.colors.sequential.Reds,
                    labels={'Anomaly': 'Anomaly Count'})
fig_map.update_layout(coloraxis_colorbar=dict(title="Anomaly Count", thicknessmode="pixels", thickness=20, lenmode="pixels", len=200))
fig_map.write_html("/home/ubuntu/choropleth_map.html")
fig_map.write_image("/home/ubuntu/choropleth_map.png")

# 2. Refined Anomaly Score Distribution
scores_pd = df_results.select("anomaly_score", "is_anomaly").sample(False, 0.01).toPandas()
fig_dist = px.histogram(scores_pd, x="anomaly_score", color="is_anomaly", 
                   title="Distribution of Anomaly Scores", barmode="overlay",
                   labels={"anomaly_score": "Anomaly Score", "is_anomaly": "Is Anomaly"},
                   color_discrete_map={True: "red", False: "blue"})
fig_dist.update_layout(xaxis_title="Anomaly Score", yaxis_title="Frequency", legend_title="Status")
fig_dist.write_html("/home/ubuntu/score_distribution.html")
fig_dist.write_image("/home/ubuntu/score_distribution.png")

# 3. Refined Top 10 AWS Services
source_stats = df_results.filter(df_results.is_anomaly == True).groupBy("eventSource").count().sort("count", ascending=False).limit(10).toPandas()
source_stats['eventSource'] = source_stats['eventSource'].str.replace('.amazonaws.com', '', regex=False)
fig_source = px.bar(source_stats, x="eventSource", y="count", title="Top 10 AWS Services with Anomalies",
                   labels={"eventSource": "AWS Service", "count": "Anomaly Count"},
                   color="count", color_continuous_scale=px.colors.sequential.Reds)
fig_source.update_layout(xaxis_title="AWS Service", yaxis_title="Anomaly Count", coloraxis_showscale=False)
fig_source.write_html("/home/ubuntu/top_sources.html")
fig_source.write_image("/home/ubuntu/top_sources.png")

# 4. Refined Heatmap: Event Name vs Error Code (Top 10 x Top 10 for clarity)
anomaly_df = df_results.filter(df_results.is_anomaly == True)
top_events = [r['eventName'] for r in anomaly_df.groupBy("eventName").count().sort("count", ascending=False).limit(10).collect()]
top_errors = [r['errorCode'] for r in anomaly_df.groupBy("errorCode").count().sort("count", ascending=False).limit(10).collect()]

heatmap_data = anomaly_df.filter(col("eventName").isin(top_events) & col("errorCode").isin(top_errors)) \
                        .groupBy("eventName", "errorCode").count().toPandas()

fig_heatmap = px.density_heatmap(heatmap_data, x="eventName", y="errorCode", z="count",
                            title="Anomaly Heatmap: Top Events vs Error Codes",
                            labels={"eventName": "Event Name", "errorCode": "Error Code", "count": "Frequency"},
                            color_continuous_scale="Reds")
fig_heatmap.update_layout(xaxis_title="Event Name", yaxis_title="Error Code")
fig_heatmap.write_html("/home/ubuntu/anomaly_heatmap.html")
fig_heatmap.write_image("/home/ubuntu/anomaly_heatmap.png")

print("All refined visualizations generated.")
spark.stop()

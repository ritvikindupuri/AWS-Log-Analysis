from pyspark.sql import SparkSession
from pyspark.ml.clustering import KMeans
from pyspark.sql.functions import col, udf
from pyspark.sql.types import DoubleType, BooleanType
import numpy as np

# Initialize Spark Session
spark = SparkSession.builder.appName("AnomalyDetectionModel").getOrCreate()

# Load filtered data
df_original = spark.read.parquet("/home/ubuntu/filtered_data.parquet")

# Re-run transformation
from pyspark.ml.feature import StringIndexer, VectorAssembler, OneHotEncoder
from pyspark.ml import Pipeline

selected_cols = ['eventSource', 'eventName', 'awsRegion', 'userIdentitytype', 'eventType', 'errorCode']
indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_index", handleInvalid="keep") for c in selected_cols]
encoders = [OneHotEncoder(inputCol=f"{c}_index", outputCol=f"{c}_vec") for c in selected_cols]
assembler = VectorAssembler(inputCols=[f"{c}_vec" for c in selected_cols], outputCol="features")
pipeline = Pipeline(stages=indexers + encoders + [assembler])
model_pipeline = pipeline.fit(df_original)
df_combined = model_pipeline.transform(df_original)

# Train KMeans
kmeans = KMeans(k=10, seed=1)
model_kmeans = kmeans.fit(df_combined)

# Make predictions
predictions = model_kmeans.transform(df_combined)

# Calculate distance to cluster center as anomaly score
centers = model_kmeans.clusterCenters()

def calculate_distance(features, prediction):
    center = centers[prediction]
    return float(np.linalg.norm(features.toArray() - center))

distance_udf = udf(calculate_distance, DoubleType())
predictions_with_score = predictions.withColumn("anomaly_score", distance_udf(col("features"), col("prediction")))

# Based on previous check, 95th percentile is around 1.8
threshold = 1.8

print(f"Using fixed threshold: {threshold}")

predictions_with_score = predictions_with_score.withColumn("is_anomaly", col("anomaly_score") >= threshold)

# Save results
predictions_with_score.select(selected_cols + ["anomaly_score", "is_anomaly"]).write.mode("overwrite").parquet("/home/ubuntu/anomaly_results.parquet")

print(f"Model training complete. Threshold: {threshold}")
spark.stop()

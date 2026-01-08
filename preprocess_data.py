from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, isnan, udf
from pyspark.ml.feature import StringIndexer, VectorAssembler, OneHotEncoder
from pyspark.ml import Pipeline
import pandas as pd

# Initialize Spark Session
spark = SparkSession.builder.appName("AnomalyDetectionPreprocessing").getOrCreate()

# Load the dataset
df = spark.read.csv("/home/ubuntu/upload/dec12_18features.csv", header=True, inferSchema=True)

# Drop rows with many nulls or irrelevant columns
# For anomaly detection, we'll focus on: eventSource, eventName, awsRegion, userIdentitytype, eventType, errorCode
selected_cols = ['eventSource', 'eventName', 'awsRegion', 'userIdentitytype', 'eventType', 'errorCode']
df_filtered = df.select(selected_cols).dropna()

# Indexing and Encoding categorical features
indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_index", handleInvalid="keep") for c in selected_cols]
encoders = [OneHotEncoder(inputCol=f"{c}_index", outputCol=f"{c}_vec") for c in selected_cols]

# Assemble features into a single vector
assembler = VectorAssembler(inputCols=[f"{c}_vec" for c in selected_cols], outputCol="features")

# Create a pipeline
pipeline = Pipeline(stages=indexers + encoders + [assembler])

# Fit and transform the data
model = pipeline.fit(df_filtered)
df_preprocessed = model.transform(df_filtered)

# Save the preprocessed data (only features) for ML
# Since we'll use Isolation Forest (common for anomalies), we might need to convert to pandas if the dataset size allows, 
# or use Spark's native ML if available. Spark doesn't have a built-in Isolation Forest in 3.5.0, 
# but we can use KMeans or other clustering methods, or sample for sklearn.
# Given the size (1.9M rows), let's try to use Spark's KMeans for anomaly detection (distance from centroid).

# Alternatively, we can use a sample for sklearn's Isolation Forest if we want that specific model.
# Let's stick to Spark ML for scalability.

df_preprocessed.select("features").write.mode("overwrite").parquet("/home/ubuntu/preprocessed_features.parquet")

# Also save the original filtered data for visualization later
df_filtered.write.mode("overwrite").parquet("/home/ubuntu/filtered_data.parquet")

print("Preprocessing complete. Data saved.")
spark.stop()

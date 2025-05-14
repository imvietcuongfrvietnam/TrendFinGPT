from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType

# Khởi tạo SparkSession
spark = SparkSession.builder \
    .appName("KafkaToElastic") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.elasticsearch:elasticsearch-spark-30_2.12:8.13.4") \
    .config("spark.executor.memory", "1g") \
    .config("spark.driver.memory", "1g") \
    .getOrCreate()

# Định nghĩa schema bài viết
schema = StructType() \
    .add("title", StringType()) \
    .add("summary", StringType()) \
    .add("url", StringType()) \
    .add("author", StringType()) \
    .add("content", StringType()) \
    .add("date", StringType())

# Đọc stream từ Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "vietnamnet_articles") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON từ Kafka
parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Ghi vào Elasticsearch
parsed.writeStream \
    .format("org.elasticsearch.spark.sql") \
    .option("es.nodes", "elasticsearch") \
    .option("es.resource", "vietnamnet") \
    .option("es.nodes.wan.only", "true") \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .outputMode("append") \
    .start() \
    .awaitTermination()
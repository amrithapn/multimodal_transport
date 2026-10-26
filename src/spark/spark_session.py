"""
Create a reusable Spark Session.
"""

from pyspark.sql import SparkSession


def create_spark_session():
    spark = (
        SparkSession.builder
        .appName("MultimodalTransportCA")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return spark


if __name__ == "__main__":
    spark = create_spark_session()

    print("=" * 60)
    print("Spark Session Created Successfully")
    print("=" * 60)

    print(f"Spark Version : {spark.version}")

    spark.stop()

username = "bob"
password_with_token = "bobXXXX"


import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
  
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

username = "eric.russia97@gmail.com"
password = "Ozg0&WgLb6jTsg7"

# get this here: https://docs.idalko.com/exalate/display/ED/Salesforce%3A+How+to+generate+a+security+token
security_token = "lVqxLRwIFZsyVFLRYlT4FvSwf"

password_with_token = password + security_token

SOQL = "SELECT name, industry, type, billingaddress, sic FROM account LIMIT 5"

df = (
    spark
        .read
        .format("com.springml.spark.salesforce")
        .option("username", username)
        .option("password", password_with_token)
        .option("soql", SOQL)
        .load()
)

print(df.show())

job.commit()
job.run()
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from dataclasses import dataclass

from typing import List, Optional, OrderedDict, Type
from simple_salesforce import Salesforce, SFType

#####################
# --- Constants --- #
#####################

username = "some-username"
password = "some-password"

# get this here: https://docs.idalko.com/exalate/display/ED/Salesforce%3A+How+to+generate+a+security+token
security_token = "some-token"

password_with_token = password + security_token


#####################
# --- Spark Job --- #
#####################

def run():
    sc = SparkContext.getOrCreate()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)

    soql = "SELECT Phone from account"

    df = (
        spark
            .read
            .format("com.springml.spark.salesforce")
            .option("username", username)
            .option("password", password_with_token)
            .option("soql", soql)
            .option("bulk", True)
            # Opportunity.LastStageChangeDate is only availaable in API v52
            .option("version", 52)
            .option("sfObject", "account")
            .load()
    )

run()

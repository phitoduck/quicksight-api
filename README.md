# Quicksight Dashboards

This repository is for a project that does the following:

1. Extracts data from Salesforce.com using AWS Glue (an ETL job)
2. Lands that data into S3
3. Builds a series of Athena tables via Athena Queries in AWS Step Functions
4. Exposes dashboards in AWS Quicksight with some visualizations from the data

Here are some helpful resources that this repo is patterned from:

1. [Salesforce/Pyspark tutorial](https://www.jitsejan.com/integrating-pyspark-with-salesforce) by JJ's world
2. An [AWS blogpost](https://aws.amazon.com/blogs/big-data/develop-and-test-aws-glue-version-3-0-jobs-locally-using-a-docker-container/) for developing Glue Jobs locally (because running Notebooks in the console gets expensive quickly and... local unit tests are good)
3. An [AWS blogpost](https://aws.amazon.com/blogs/big-data/extracting-salesforce-com-data-using-aws-glue-and-analyzing-with-amazon-athena/) about extracting Salesforce data into Athena using Glue


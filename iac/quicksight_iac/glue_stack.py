from pathlib import Path
from aws_cdk import Stack, CfnOutput
from constructs import Construct
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam

import aws_cdk as cdk

from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets

from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_glue_alpha as glue_alpha

THIS_DIR = Path(__file__).parent
MAVEN_JARS_DIR = THIS_DIR / "../resources/glue/volumes/maven_jars/"

class GlueStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "glue-dependencies-bucket",
            bucket_name="glue-dependencies-bucket-experiment",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            public_read_access=False
        )

        # WARNING! Do not use this for large numbers of files.
        # CDK moves the items to the CDKToolkit bucket first, then
        # copies them to the final destination. This can be extremely slow.
        s3_deployment.BucketDeployment(
            self,
            "maven-jars-for-glue",
            sources=[
                s3_deployment.Source.asset(str(MAVEN_JARS_DIR))
            ],
            destination_bucket=bucket,
        )

        glue_alpha.JobExecutable.python_etl(
            extra_files=1,
            extra_jars=...,
            extra_jars_first=...,
            extra_python_files=...,
            glue_version=glue_alpha.GlueVersion.V2_0,
            script=...,
            python_version=glue_alpha.PythonVersion.THREE,
        )

        glue_alpha.Job(
            self,
            "salesforce-ingest-job"
            worker_count=1,
            max_retries=2,
            executable=...,
        )


    
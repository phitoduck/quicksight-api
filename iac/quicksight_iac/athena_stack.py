from pathlib import Path
from typing import List, Tuple
from aws_cdk import Stack, CfnOutput
from constructs import Construct
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam

import aws_cdk as cdk

from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_secretsmanager as secretsmanager

from aws_cdk import aws_s3 as s3
from aws_cdk import aws_glue_alpha as glue
from aws_cdk import aws_glue as glue_cfn
from aws_cdk import aws_s3_deployment as s3_deployment

SALESFORCE_OBJ_NAMES = ["account", "opportunity"]


class AthenaCustomerStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        customer_org_name: str,
        datalake_bucket_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.namer = lambda name: f"{customer_org_name}-{name}"

        datalake_bucket = s3.Bucket.from_bucket_name(
            self,
            id=self.namer("datalake_bucket"),
            bucket_name=datalake_bucket_name,
        )

        customer_org_database = glue.Database(
            self,
            id=self.namer("database"),
            database_name=customer_org_name,
        )

        self.make_glue_crawler(
            customer_org_name=customer_org_name,
            salesforce_object_names=SALESFORCE_OBJ_NAMES,
            customer_org_database=customer_org_database,
            datalake_bucket=datalake_bucket,
        )

        # customer_tables: List[glue.Table] = self.make_tables_for_customer_org(
        #     salesforce_object_names=SALESFORCE_OBJ_NAMES,
        #     customer_org_name=customer_org_name,
        #     datalake_bucket=datalake_bucket,
        #     customer_org_database=customer_org_database,
        # )

    # def make_tables_for_customer_org(
    #     self,
    #     salesforce_object_names: List[str],
    #     customer_org_name: str,
    #     datalake_bucket: s3.Bucket,
    #     customer_org_database: glue.Database,
    # ) -> List[glue.Table]:
    #     return [
    #         glue.Table(
    #             self,
    #             id=self.namer(name=f"{salesforce_obj}-table"),
    #             bucket=datalake_bucket,
    #             s3_prefix=f"org_name={customer_org_name}/sf_object={salesforce_obj}",
    #             database=customer_org_database,
    #             table_name=salesforce_obj.strip().lower(),
    #             data_format=glue.DataFormat.PARQUET,
    #         )
    #         for salesforce_obj in salesforce_object_names
    #     ]

    def make_glue_crawler(
        self,
        customer_org_name: str,
        salesforce_object_names: List[str],
        customer_org_database: glue.Database,
        datalake_bucket: s3.Bucket,
    ) -> glue_cfn.CfnCrawler:
        crawler_role = iam.Role(
            self,
            id=self.namer("glue-crawler-role"),
            description="Assigns the managed policy AWSGlueServiceRole to AWS Glue Crawler so it can crawl S3 buckets",
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    self.namer("managed-glue-service-role-policy"),
                    "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
                ),
            ],
            assumed_by=iam.ServicePrincipal(service="glue.amazonaws.com"),
        )

        # grant crawler role permission to access S3 objects under the customer org prefix
        crawler_role.attach_inline_policy(
            policy=iam.Policy(
                self,
                self.namer("read-access-to-customer-objs-policy"),
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:GetObject"],
                        resources=[
                            datalake_bucket.bucket_arn + f"/{customer_org_name}*"
                        ],
                    )
                ],
            ),
        )

        glue_cfn.CfnCrawler(
            self,
            id=self.namer("crawler"),
            description=f"Crawl S3 to update all tables belonging to: {customer_org_name}",
            database_name=customer_org_database._physical_name,
            role=crawler_role.role_name,
            targets=glue_cfn.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue_cfn.CfnCrawler.S3TargetProperty(
                        path=datalake_bucket.s3_url_for_object(
                            key=f"{customer_org_name}/{salesforce_obj}/"
                        )
                    )
                    for salesforce_obj in salesforce_object_names
                ]
            ),
        )

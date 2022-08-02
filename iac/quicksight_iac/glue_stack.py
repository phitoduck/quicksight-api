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
from aws_cdk import aws_s3_deployment as s3_deployment

THIS_DIR = Path(__file__).parent
GLUE_DIR = (THIS_DIR / "../resources/glue").resolve().absolute()
MAVEN_JARS_DIR = GLUE_DIR / "volumes/maven_jars/"
GLUE_ETL_JOB__PYTHON_SCRIPT__FPATH = GLUE_DIR / "volumes/jupyter/salesforce.py"

DEVELOPMENT_SF_CREDENTIALS_SECRET_ID = "sf-credentials"


class GlueStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        jars_bucket: s3.Bucket = self.make_bucket_for_etl_script_dependencies()
        self.etl_output_bucket: s3.Bucket = self.make_output_bucket_for_etl_job()

        maven_jar_s3_keys, maven_jarfile_deployment = self.upload_maven_jars_to_bucket(
            bucket=jars_bucket, jarfile_prefix="maven-jars/"
        )

        etl_job: glue.Job = self.make_glue_job(
            maven_jar_s3_keys=maven_jar_s3_keys,
            maven_jarfile_deployment=maven_jarfile_deployment,
            etl_output_bucket=self.etl_output_bucket,
        )

        self.authorize_etl_job_to_access_secrets(etl_job=etl_job)

    def make_glue_job(
        self,
        maven_jar_s3_keys: List[str],
        maven_jarfile_deployment: s3_deployment.BucketDeployment,
        etl_output_bucket: s3.Bucket,
    ) -> glue.Job:

        etl_python_script: glue.Code = self.get_glue_python_script()

        etl_job = glue.Job(
            self,
            "salesforce-ingest-job",
            worker_count=2,
            worker_type=glue.WorkerType.G_1_X,
            max_retries=0,
            executable=glue.JobExecutable.python_etl(
                extra_jars=[
                    glue.Code.from_bucket(
                        bucket=maven_jarfile_deployment.deployed_bucket,
                        key=jar_s3_key,
                    )
                    for jar_s3_key in maven_jar_s3_keys
                ],
                # extra_jars_first=True,
                glue_version=glue.GlueVersion.V2_0,
                script=etl_python_script,
                python_version=glue.PythonVersion.THREE,
            ),
            # list of arguments here: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-glue-arguments.html
            default_arguments={
                # comma separated list of (s3:// paths to .whl files) or (requirements.txt formatted pip statements)
                # see documentation here: https://aws.amazon.com/premiumsupport/knowledge-center/glue-version2-external-python-libraries/
                "--additional-python-modules": "simple-salesforce==1.12.1",
                "--custom__output_bucket_name": etl_output_bucket.bucket_name,
                "--custom__customer_org_name": "development",
            },
        )

        etl_output_bucket.grant_read_write(etl_job.role)

        # ensure the jar files are uploaded before the job is created
        etl_job.node.add_dependency(maven_jarfile_deployment)

        return etl_job

    def make_bucket_for_etl_script_dependencies(self) -> s3.Bucket:
        return s3.Bucket(
            self,
            "maven-jars-bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            # delete s3 objects on "cdk destroy" so we don't have to manually delete them
            auto_delete_objects=True,
        )

    def make_output_bucket_for_etl_job(self) -> s3.Bucket:
        return s3.Bucket(
            self,
            "etl-output-bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            # delete s3 objects on "cdk destroy" so we don't have to manually delete them
            # TODO: remove this when we have real production data
            auto_delete_objects=True,
        )

    def upload_maven_jars_to_bucket(
        self, bucket: s3.Bucket, jarfile_prefix: str
    ) -> Tuple[List[str], s3_deployment.BucketDeployment]:
        """
        Upload each .jar file to the S3 bucket and return:

        - a list of S3 object keys (everything after s3://bucket-name/)
        - the s3 deployment object
        """
        jar_fpaths: List[Path] = list(MAVEN_JARS_DIR.glob("*.jar"))
        from rich.pretty import pprint

        print("jar_fpaths")
        pprint(jar_fpaths)

        bucket_deployment = s3_deployment.BucketDeployment(
            self,
            "etl-maven-jar-files",
            sources=[
                # if we point this at individual jar files, CDK will "unzip" them
                # and the .jar innards will spill out into the S3 bucket. Instead,
                # we point the source to the local directory containing all of the jar files.
                s3_deployment.Source.asset(path=str(MAVEN_JARS_DIR)),
            ],
            destination_bucket=bucket,
            destination_key_prefix=jarfile_prefix,
        )

        def make_jarfile_s3_key(jar_fpath: Path) -> str:
            obj_key = jarfile_prefix + jar_fpath.name
            return obj_key

        jarfile_s3_keys = [make_jarfile_s3_key(jar_fpath) for jar_fpath in jar_fpaths]
        return jarfile_s3_keys, bucket_deployment

    # pylint: disable=pointless-string-statement
    """
    NOTE: glue.Code.from_asset successfully uploaded the files to S3, but the s3 keys
    were CDK-generated gibberish names. The ETL job complained about not having the jarfiles
    and it became difficult to verify that all the correct jar files were present because
    of the non-human-readable S3 keys. Previously, a normal S3 deployment had worked
    so I reverted back to that approach. See self.upload_maven_jars_to_bucket()
    """
    # def get_maven_jar_assets(self) -> List[glue.Code]:
    #     """Create a ``glue.Code`` object for each ``.jar`` file in ``maven_jars/``."""
    #     jar_fpaths: List[Path] = list(MAVEN_JARS_DIR.glob("*.jar"))
    #     return [glue.Code.from_asset(path=str(jar_fpath)) for jar_fpath in jar_fpaths]

    def get_glue_python_script(self) -> glue.Code:
        return glue.Code.from_asset(
            path=str(GLUE_ETL_JOB__PYTHON_SCRIPT__FPATH),
        )

    def authorize_etl_job_to_access_secrets(self, etl_job: glue.Job):
        developer_sf_creds_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "development-sf-credentials-secret",
            secret_name=DEVELOPMENT_SF_CREDENTIALS_SECRET_ID,
        )

        developer_sf_creds_secret.grant_read(etl_job.role)

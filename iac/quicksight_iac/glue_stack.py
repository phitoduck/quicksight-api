from pathlib import Path
from typing import List
from aws_cdk import Stack, CfnOutput
from constructs import Construct
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam

import aws_cdk as cdk

from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_secretsmanager as secretsmanager

from aws_cdk import aws_s3 as s3
from aws_cdk import aws_glue_alpha as glue

THIS_DIR = Path(__file__).parent
GLUE_DIR = (THIS_DIR / "../resources/glue").resolve().absolute()
MAVEN_JARS_DIR = GLUE_DIR / "volumes/maven_jars/"
GLUE_ETL_JOB__PYTHON_SCRIPT__FPATH = GLUE_DIR / "volumes/jupyter/salesforce.py"

DEVELOPMENT_SF_CREDENTIALS_SECRET_ID = "sf-credentials"


class GlueStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        etl_job: glue.Job = self.make_glue_job()
        self.authorize_etl_job_to_access_secrets(etl_job=etl_job)

    def make_glue_job(self) -> glue.Job:

        etl_python_script: glue.Code = self.get_glue_python_script()
        jar_files: List[glue.Code] = self.get_maven_jar_assets()

        return glue.Job(
            self,
            "salesforce-ingest-job",
            worker_count=2,
            worker_type=glue.WorkerType.G_1_X,
            max_retries=0,
            executable=glue.JobExecutable.python_etl(
                extra_jars=jar_files,
                extra_jars_first=True,
                glue_version=glue.GlueVersion.V2_0,
                script=etl_python_script,
                python_version=glue.PythonVersion.THREE,
            ),
            # list of arguments here: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-glue-arguments.html
            default_arguments={
                # comma separated list of (s3:// paths to .whl files) or (requirements.txt formatted pip statements)
                # see documentation here: https://aws.amazon.com/premiumsupport/knowledge-center/glue-version2-external-python-libraries/
                "--additional-python-modules": "simple-salesforce==1.12.1"
            },
        )

    def get_maven_jar_assets(self) -> List[glue.Code]:
        """Create a ``glue.Code`` object for each ``.jar`` file in ``maven_jars/``."""
        jar_fpaths: List[Path] = list(MAVEN_JARS_DIR.glob("*.jar"))
        return [glue.Code.from_asset(path=str(jar_fpath)) for jar_fpath in jar_fpaths]

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

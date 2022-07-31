"""
WARNING!!!

This file is deprecated.

For some unknown reason, creating the lambda in this stack
and then using lambda_.from_lookup() in the api gateway stack
caused the API Gateway not have IAM permissions to invoke the function.

I tried many approaches to manually make the authorization happen, but
ultimately I gave up and moved the lambda creation logic to that stack.
"""

from pathlib import Path
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
import aws_cdk as cdk

THIS_DIR = Path(__file__).parent
LAMBDA_CODE_DIR = THIS_DIR / "../../backend_api"


class QuicksightApiLambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        # role_arn_assumed_by_users: str,
        # cognito_domain_url: str,xw
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.func = lambda_.Function(
            self,
            "quicksight-manage-user-api-lambda",
            timeout=cdk.Duration.seconds(30),
            memory_size=512,
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=lambda_.Code.from_asset(
                path=str(LAMBDA_CODE_DIR),
                bundling=cdk.BundlingOptions(
                    image=cdk.DockerImage.from_registry(
                        image="lambci/lambda:build-python3.8"
                    ),
                    command=[
                        "bash",
                        "-c",
                        "mkdir -p /asset-output"
                        + " && pip install .[lambda] -t /asset-output"
                        + " && cp -r ./aws-lambda/index.py /asset-output/"
                        + " && rm -rf /asset-output/boto3 /asset-output/botocore",
                    ],
                ),
            ),
            environment={
                
            },
        )

        # allow the role to manage quicksight users and create embed URLs for them
        self.func.role.attach_inline_policy(
            policy=iam.Policy(
                self,
                "allow-lambda-to-manage-quicksight-users",
                document=iam.PolicyDocument.from_json(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": [
                                    "quicksight:GenerateEmbedUrlForRegisteredUser",
                                    "quicksight:SearchDashboards",
                                    "quicksight:DescribeUser",
                                    "quicksight:RegisterUser",
                                    "quicksight:CreateGroup",
                                    "quicksight:CreateGroupMembership",
                                ],
                                "Resource": "*",
                                "Effect": "Allow",
                            },
                            {
                                "Action": [
                                    "logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                ],
                                "Resource": "*",
                                "Effect": "Allow",
                            },
                        ],
                    }
                ),
            )
        )

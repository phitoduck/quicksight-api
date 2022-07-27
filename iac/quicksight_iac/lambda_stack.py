from pathlib import Path
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
import aws_cdk as cdk

THIS_DIR = Path(__file__).parent
LAMBDA_CODE_DIR = THIS_DIR / "../../quicksight-lambda"


class LambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        role_arn_assumed_by_users: str,
        cognito_domain_url: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.func = lambda_.Function(
            self,
            "quicksight-manage-users-lambda",
            timeout=cdk.Duration.seconds(30),
            memory_size=512,
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="quicksight_lambda.handler.lambda_handler",
            code=lambda_.Code.from_asset(
                path=str(LAMBDA_CODE_DIR),
                bundling=cdk.BundlingOptions(
                    # learn about this here:
                    # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_lambda/README.html#bundling-asset-code
                    # Using this lambci image makes it so that dependencies with C-binaries compile correctly for the lambda runtime.
                    # The AWS CDK python images were not doing this. Relevant dependencies are: pandas, asyncpg, and psycogp2-binary.
                    image=cdk.DockerImage.from_registry(
                        image="lambci/lambda:build-python3.8"
                    ),
                    command=[
                        "bash",
                        "-c",
                        "mkdir -p /asset-output"
                        + " && pip install ./ -t /asset-output"
                        + " && cp -r quicksight_lambda/content/ /asset-output/quicksight_lambda/"
                        + " && cp -r quicksight_lambda/quicksight/ /asset-output/quicksight_lambda/"
                        # + "&& rm -rf /asset-output/boto3 /asset-output/botocore",
                    ],
                ),
            ),
            environment={
                "AwsAccountId": self.account,
                "Email": "eric.riddoch@bengroup.com",
                "DashboardId": "e611f35c-7026-4bc1-a01b-934aba93bd47",
                "RoleArn": role_arn_assumed_by_users,
                "QuickSightIdentityRegion": "us-east-1",
                "DashboardRegion": "us-east-2",
                "AWS_DATA_PATH": ".",
                "CognitoDomainUrl": cognito_domain_url,
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

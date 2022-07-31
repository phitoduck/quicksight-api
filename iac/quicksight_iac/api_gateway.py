from pathlib import Path
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_apigatewayv2_alpha as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers_alpha as apigwv2_authorizers
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigwv2_integrations
from aws_cdk import aws_logs as logs
from aws_cdk import aws_apigatewayv2 as apigwv2_cfn
from aws_cdk import aws_iam as iam

from aws_cdk import aws_route53 as route53

import aws_cdk as cdk

THIS_DIR = Path(__file__).parent
LAMBDA_CODE_DIR = THIS_DIR / "../../backend_api"

class ApiGatewayStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        # lambda_handler_arn: str,
        # lambda_handler: lambda_.Function,
        apigw_domain_name: apigwv2.DomainName,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api = apigwv2.HttpApi(
            self,
            "api-gateway",
            default_domain_mapping=apigwv2.DomainMappingOptions(
                domain_name=apigw_domain_name
            ),
            create_default_stage=True,
        )

        self.test_stage = self.api.add_stage(
            "test-stage", 
            auto_deploy=True, 
            stage_name="test",
        )
        
        self.enable_access_logs_for_stage(stage=self.test_stage)
        self.enable_access_logs_for_stage(stage=self.api.default_stage)

        # lambda_handler = lambda_.Function.from_function_arn(
        #     self, "embed-sample-lambda-handler", function_arn=lambda_handler_arn
        # )

        lambda_handler: lambda_.Function = self.create_quicksight_api_lambda_handler()

        lambda_handler.add_permission(
            "api-invoke-handler-permission",
            principal=iam.ServicePrincipal(service="apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{self.api.api_id}/*"
        )

        lambda_integration = apigwv2_integrations.HttpLambdaIntegration(
            "embed-sample-lambda-integration",
            handler=lambda_handler,
        )


        # lambda_handler.grant_invoke(lambda_integration)

        self.api.add_routes(
            path="/{proxy+}",
            methods=[apigwv2.HttpMethod.GET],
            integration=lambda_integration
        )


    def enable_access_logs_for_stage(self, stage: apigwv2.HttpStage):

        apigw_access_log_group = logs.LogGroup(
            self,
            stage.node.id + "-access-logs-group",
            retention=logs.RetentionDays.ONE_DAY,
        )

        test_stage_cfn: apigwv2_cfn.CfnStage = self.test_stage.node.default_child
        test_stage_cfn.access_log_settings = {
            "destinationArn": apigw_access_log_group.log_group_arn,
            "format": """$context.identity.sourceIp - - [$context.requestTime] "$context.httpMethod $context.routeKey $context.protocol" $context.status $context.responseLength $context.requestId $context.error.message $context.integrationErrorMessage"""
        }

    def create_quicksight_api_lambda_handler(self) -> lambda_.Function:
        func = lambda_.Function(
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
        func.role.attach_inline_policy(
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

        return func



        # api: apigwv2.IHttpApi = apigwv2.HttpApi.from_http_api_attributes(
        #     self,
        #     "api-gateway-now-adding-endpoints",
        #     http_api_id=api_gateway_id,
        # )

        # apigwv2.HttpRoute(
        #     self,
        #     "embed-sample-route",
        #     route_key=apigwv2.HttpRouteKey.with_(
        #         path=EMBED_SAMPLE_ENDPOINT, method=apigwv2.HttpMethod.GET
        #     ),
        #     http_api=api,
        #     integration=
        # )

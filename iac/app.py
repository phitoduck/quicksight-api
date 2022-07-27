#!/usr/bin/env python3
import os

import aws_cdk as cdk
from quicksight_iac.api_gateway import ApiGatewayRoutesStack, ApiGatewayStack
from quicksight_iac.cognito_stack import CognitoStack
from quicksight_iac.lambda_stack import LambdaStack

# from iac.iac_stack import IacStack
from quicksight_iac.s3_static_site_stack import S3StaticSiteStack

BEN_AI_SANDBOX = "093262366795"
environment = cdk.Environment(account=BEN_AI_SANDBOX, region="us-east-2")

app = cdk.App()
# IacStack(app, "IacStack",
#     # If you don't specify 'env', this stack will be environment-agnostic.
#     # Account/Region-dependent features and context lookups will not work,
#     # but a single synthesized template can be deployed anywhere.

#     # Uncomment the next line to specialize this stack for the AWS Account
#     # and Region that are implied by the current CLI configuration.

#     #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

#     # Uncomment the next line if you know exactly what Account and Region you
#     # want to deploy the stack to. */

#     #env=cdk.Environment(account='123456789012', region='us-east-1'),

#     # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
#     )

static_site_stack = S3StaticSiteStack(
    app,
    "quicksight-static-site",
    domain_name="ben-ai-sandbox.com",
    subdomain="quicksight",
    env=environment,
)

api_gateway_stack = ApiGatewayStack(
    app,
    "quicksight-api-gateway",
    env=environment,
)

cognito_stack = CognitoStack(
    app,
    "cognito-stack",
    frontend_domain=static_site_stack.cloudfront_distribution.domain_name,
    embed_sample_route_url=api_gateway_stack.embed_sample_route,
    env=environment,
)

lambda_stack = LambdaStack(
    app,
    "quicksight-lambda-stack",
    role_arn_assumed_by_users=cognito_stack.quicksight_role_assumed_by_cognito_users.role_arn,
    cognito_domain_url=cognito_stack.user_pool_domain.base_url(),
    env=environment,
)

stack_adding_endpoints_to_api_gateway = ApiGatewayRoutesStack(
    app,
    "api-gateway-routes",
    api_gateway_id=api_gateway_stack.api.http_api_id,
    lambda_handler_arn=lambda_stack.func.function_arn,
    env=environment,
)


app.synth()

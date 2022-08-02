#!/usr/bin/env python3
import os

# from quicksight_iac.quicksight_api_lambda_stack import QuicksightApiLambdaStack
# from quicksight_iac.lambda_stack import LambdaStack
import aws_cdk as cdk
from quicksight_iac.athena_stack import AthenaCustomerStack
from quicksight_iac.glue_stack import GlueStack
from quicksight_iac.subdomains_stack import SubdomainsStack
from quicksight_iac.api_gateway import ApiGatewayStack
from quicksight_iac.cognito_stack import CognitoStack

# from iac.iac_stack import IacStack
from quicksight_iac.s3_static_site_stack import S3StaticSiteStack

BEN_AI_SANDBOX = "093262366795"
environment = cdk.Environment(account=BEN_AI_SANDBOX, region="us-east-2")

SUBDOMAIN = "api.ben-de-sandbox.com"
COGNITO_LOGIN_REDIRECT_URL = f"https://{SUBDOMAIN}/hello"

app = cdk.App()

cognito_stack = CognitoStack(
    app,
    "cognito-stack",
    # frontend_domain=static_site_stack.cloudfront_distribution.domain_name,
    embed_sample_route_url=COGNITO_LOGIN_REDIRECT_URL,
    top_level_auth_domain="ben-de-sandbox.com",
    auth_subdomain="login",
    env=environment,
)


subdomains_stack = SubdomainsStack(
    app,
    "quicksight-subdomains",
    api_gateway_subdomain="api",
    top_level_domain="ben-de-sandbox.com",
    env=environment,
)

api_gateway_stack = ApiGatewayStack(
    app,
    "quicksight-api-gateway",
    env=environment,
    apigw_domain_name=subdomains_stack.apigw_domain_name,
)

glue_stack = GlueStack(app, "quicksight-glue", env=environment)

AthenaCustomerStack(
    app,
    "development-org-crawler-stack",
    customer_org_name="development",
    datalake_bucket_name=glue_stack.etl_output_bucket.bucket_name,
    env=environment,
)

app.synth()


# static_site_stack = S3StaticSiteStack(
#     app,
#     "quicksight-static-site",
#     domain_name="ben-ai-sandbox.com",
#     subdomain="quicksight",
#     env=environment,
# )

# lambda_stack = LambdaStack(
#     app,
#     "quicksight-lambda-stack",
#     role_arn_assumed_by_users=cognito_stack.quicksight_role_assumed_by_cognito_users.role_arn,
#     cognito_domain_url=cognito_stack.user_pool_domain.base_url(),
#     env=environment,
# )

# api_lambda_stack = QuicksightApiLambdaStack(
#     app,
#     "quicksite-api-lambda",
#     env=environment,
# )

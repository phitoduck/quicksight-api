from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_apigatewayv2_alpha as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers_alpha as apigwv2_authorizers
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigwv2_integrations

EMBED_SAMPLE_ENDPOINT = "/embed-sample"


class ApiGatewayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api = apigwv2.HttpApi(
            self,
            "api-gateway",
        )

        self.test_stage = self.api.add_stage(
            "test-stage", auto_deploy=True, stage_name="test"
        )

    @property
    def embed_sample_route(self) -> str:
        return self.test_stage.url + EMBED_SAMPLE_ENDPOINT


class ApiGatewayRoutesStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api_gateway_id: str,
        lambda_handler_arn: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api: apigwv2.IHttpApi = apigwv2.HttpApi.from_http_api_attributes(
            self,
            "api-gateway-now-adding-endpoints",
            http_api_id=api_gateway_id,
        )

        # api.add_routes(
        #     path=EMBED_SAMPLE_ENDPOINT,
        #     methods=[apigwv2.HttpMethod.GET],
        #     integration=
        # )

        apigwv2.HttpRoute(
            self,
            "embed-sample-route",
            route_key=apigwv2.HttpRouteKey.with_(
                path=EMBED_SAMPLE_ENDPOINT, method=apigwv2.HttpMethod.GET
            ),
            http_api=api,
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "embed-sample-lambda-integration",
                handler=lambda_.Function.from_function_arn(
                    self, "embed-sample-lambda-handler", function_arn=lambda_handler_arn
                ),
            ),
        )

from functools import lru_cache
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_apigatewayv2_alpha as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers_alpha as apigwv2_authorizers
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigwv2_integrations

from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets
from aws_cdk.aws_apigatewayv2_alpha import DomainName

from aws_cdk import aws_cognito as cognito

class SubdomainsStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        top_level_domain: str,
        api_gateway_subdomain: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        top_level_hosted_zone = self.get_top_level_hosted_zone(top_level_domain=top_level_domain)
        self.apigw_domain_name: DomainName = self.create_sub_domain_name(subdomain=api_gateway_subdomain, top_level_domain=top_level_domain, top_level_hosted_zone=top_level_hosted_zone)

        route53.ARecord(
            self,
            id="apigw-subdomain-a-record",
            record_name=f"{api_gateway_subdomain}.{top_level_domain}",
            target=route53.RecordTarget.from_alias(
                alias_target=route53_targets.ApiGatewayv2DomainProperties(
                    regional_domain_name=self.apigw_domain_name.regional_domain_name,
                    regional_hosted_zone_id=self.apigw_domain_name.regional_hosted_zone_id,
                )
            ),
            zone=top_level_hosted_zone,
        )


    def get_top_level_hosted_zone(self, top_level_domain: str) -> route53.HostedZone:
        return route53.HostedZone.from_lookup(
            self, id="parent-domain-hosted-zone", domain_name=top_level_domain
        )

    def create_sub_domain_name(self, subdomain: str, top_level_domain: str, top_level_hosted_zone: route53.HostedZone) -> DomainName:

        subdomain = f"{subdomain}.{top_level_domain}"

        cert = acm.DnsValidatedCertificate(
            self,
            id="dns-validated-cert",
            domain_name=subdomain,
            hosted_zone=top_level_hosted_zone,
            region=self.region,
        )

        domain_name = DomainName(
            self,
            id="apigw-domain-name",
            domain_name=subdomain,
            certificate=cert,
        )

        return domain_name


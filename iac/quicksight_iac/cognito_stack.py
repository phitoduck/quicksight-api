from aws_cdk import Stack, CfnOutput
from constructs import Construct
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam


class CognitoStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        embed_sample_route_url: str,
        frontend_domain: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self,
            "quicksight-cognito-user-pool",
            # quicksight requires case sensitive user names so we must enforce this at cognito
            sign_in_case_sensitive=True,
            self_sign_up_enabled=True,
            password_policy=cognito.PasswordPolicy(
                min_length=10,
                require_digits=True,
                require_lowercase=False,
                require_uppercase=False,
                require_symbols=False,
            ),
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Quicksight Temporary Password",
                email_body="Your username is {username} and temporary password is {####}",
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,
            ),
        )

        self.app_client: cognito.UserPoolClient = self.user_pool.add_client(
            "web-app-client",
            auth_flows=cognito.AuthFlow(
                admin_user_password=True,
                user_password=True,
                user_srp=True,
                custom=True,
            ),
            prevent_user_existence_errors=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL],
                callback_urls=[embed_sample_route_url],
                logout_urls=[embed_sample_route_url],
            ),
        )

        self.user_pool_domain: cognito.UserPoolDomain = self.user_pool.add_domain(
            "user-pool-domain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="quicksight-poc-eric"
            ),
        )

        self.user_pool.add_resource_server(
            "quicksight-resource-server",
            identifier="quicksight-app",
            scopes=[
                cognito.ResourceServerScope(
                    scope_name="admin",
                    scope_description="Gives the user elevated access for their organization.",
                )
            ],
        )

        openid_connect_iam_provider = iam.OpenIdConnectProvider(
            self,
            "quicksight-iam-openid-provider",
            url=self.user_pool.user_pool_provider_url,
            client_ids=[self.app_client.user_pool_client_id],
        )

        # role that can be assumed by identities from the cognito user pool;
        # this article helped figure out how to structure the conditions etc.
        # https://docs.amazonaws.cn/en_us/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
        self.quicksight_role_assumed_by_cognito_users = iam.Role(
            self,
            "web-identity-role",
            assumed_by=iam.FederatedPrincipal(
                federated=openid_connect_iam_provider.open_id_connect_provider_arn,
                assume_role_action="sts:AssumeRoleWithWebIdentity",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.user_pool.user_pool_id,
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "unauthenticated"
                    },
                },
            ),
        )

        self.quicksight_role_assumed_by_cognito_users.attach_inline_policy(
            policy=iam.Policy(
                self,
                "read-quicksight-embed-url-policy",
                document=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["quicksight:GetDashboardEmbedUrl"],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
            )
        )

        # this output is here to preserve a dependency problem
        CfnOutput(
            scope=self,
            id="static-site-index-page-url",
            value="https://" + frontend_domain + "/index.html",
            description="Url to the index page of the static site in S3",
            export_name="index-page-url-static-site",
        )
        CfnOutput(
            scope=self,
            id="user-pool-id",
            value=self.user_pool.user_pool_id,
            description="ID of the cognito user pool",
            export_name="user-pool-id",
        )
        CfnOutput(
            scope=self,
            id="user-pool-web-client-id",
            value=self.app_client.user_pool_client_id,
            description="ID of the user pool web client.",
            export_name="user-pool-web-client-id",
        )
        CfnOutput(
            scope=self,
            id="hosted-ui-base-url",
            value=self.user_pool_domain.base_url(),
            description="Base URL of the Hosted UI.",
            export_name="hosted-ui-fqdn",
        )
        CfnOutput(
            scope=self,
            id="hosted-ui-signin-url",
            value=self.user_pool_domain.sign_in_url(
                client=self.app_client, redirect_uri=embed_sample_route_url
            ),
            description="Sign in URL of the Hosted UI.",
            export_name="hosted-ui-signin-url",
        )

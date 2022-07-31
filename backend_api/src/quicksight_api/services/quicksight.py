from contextlib import contextmanager
from functools import lru_cache
from typing import Optional, Tuple
import boto3
from mypy_boto3_quicksight import QuickSightClient
from mypy_boto3_quicksight.type_defs import RegisterUserResponseTypeDef, GenerateEmbedUrlForRegisteredUserResponseTypeDef


import os
from quicksight_api.services.cognito import jwt_id_token_claims
os.environ["AWS_PROFILE"] = "ben-ai-sandbox"

print_ = print
from rich import print
from rich.pretty import pprint

QUICKSIGHT_REGION = "us-east-2"
QUICKSIGHT_IDENTITY_REGION = "us-east-1"

ACCOUNT_ID = "093262366795"
WEB_IDENTITY_IAM_ROLE_ARN = "arn:aws:iam::093262366795:role/cognito-stack-webidentityroleD0021FE2-1HDKUYYAWKBN1"
USER_POOL_ID = "us-east-2_T5XqAEdE9"
USER_POOL_CLIENT_ID = "5rk2fambn4e4td5els32ho99gt"

JWT_CLAIMS = {
  "at_hash": "1P0COYbpacaRbXqqvgfA9w",
  "sub": "bd62c1ae-02e3-4b69-9295-21bdb5724cb0",
  "email_verified": True,
  "iss": "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_T5XqAEdE9",
  "cognito:username": "eriddoch",
  "aud": "5rk2fambn4e4td5els32ho99gt",
  "event_id": "cc569c8b-4f90-46bc-8ea0-f16e98b21487",
  "token_use": "id",
  "auth_time": 1658992085,
  "exp": 1658995685,
  "iat": 1658992085,
  "jti": "c6e824dd-b887-463e-8acb-d7fb4a960d8b",
  "email": "eric.riddoch@bengroup.com"
}

@lru_cache
def get_quicksight_client(region: str) -> QuickSightClient:
    return boto3.client("quicksight", region_name=region)


@contextmanager
def register_quicksight_user(jwt_claims: dict, quicksight_identity_region: str) -> str:
    client = get_quicksight_client(region=quicksight_identity_region)
    register_response: Optional[RegisterUserResponseTypeDef] = None
    try:
        register_response: RegisterUserResponseTypeDef = client.register_user(
            AwsAccountId=ACCOUNT_ID,
            Email=jwt_claims["email"],
            SessionName=jwt_claims["cognito:username"],
            Namespace="default",
            IdentityType="IAM",
            UserRole="READER",
            ExternalLoginFederationProviderType="CUSTOM_OIDC",
            CustomFederationProviderUrl=jwt_claims["iss"],
            ExternalLoginId=jwt_claims["sub"],
            IamArn=WEB_IDENTITY_IAM_ROLE_ARN,
        )
        print(f"Registered {register_response['User']['UserName']} in quicksight")
    except client.exceptions.ResourceExistsException:
        raise Exception(f"User '{jwt_claims['email']}' already exists")

    yield register_response['User']['Arn']

    input("Press ENTER to continue and delete quicksight user...")

    client.delete_user(
        AwsAccountId=ACCOUNT_ID,
        Namespace="default",
        UserName=register_response["User"]["UserName"]
    )


def generate_embed_url_for_user(registered_user_arn: str, quicksight_region: str) -> str:
    client = get_quicksight_client(region=quicksight_region)
    embed_url_response: GenerateEmbedUrlForRegisteredUserResponseTypeDef = client.generate_embed_url_for_registered_user(
        AwsAccountId=ACCOUNT_ID,
        UserArn=registered_user_arn,
        SessionLifetimeInMinutes=15,
        ExperienceConfiguration={
            "QuickSightConsole": {"InitialPath": "/start/favorites"}
        },
    )
    return embed_url_response["EmbedUrl"]


with jwt_id_token_claims(
    email="person-3@quicksight-api.com", 
    password="test-password1",
    cognito_user_pool_id=USER_POOL_ID, 
    cognito_web_client_id=USER_POOL_CLIENT_ID, 
    user_pool_region=QUICKSIGHT_REGION,
) as jwt_claims:
    
    with register_quicksight_user(jwt_claims=jwt_claims, quicksight_identity_region=QUICKSIGHT_IDENTITY_REGION) as user_arn:

        embed_url = generate_embed_url_for_user(registered_user_arn=user_arn, quicksight_region=QUICKSIGHT_REGION)
        print_(embed_url)


# response = client.create_group_membership(
#     AwsAccountId=ACCOUNT_ID,
#     GroupName="customer-1",
#     MemberName=JWT_CLAIMS["cognito:username"],
#     Namespace="default"
# )

# example_response = {'RequestId': '7301a34d-3859-4c3f-921d-90fcd4f4fd94',
#  'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
#                                       'content-length': '730',
#                                       'content-type': 'application/json',
#                                       'date': 'Thu, 28 Jul 2022 08:04:10 GMT',
#                                       'x-amzn-requestid': '7301a34d-3859-4c3f-921d-90fcd4f4fd94'},
#                       'HTTPStatusCode': 201,
#                       'RequestId': '7301a34d-3859-4c3f-921d-90fcd4f4fd94',
#                       'RetryAttempts': 0},
#  'Status': 201,
#  'User': {'Active': False,
#           'Arn': 'arn:aws:quicksight:us-east-1:093262366795:user/default/cognito-stack-webidentityroleD0021FE2-1HDKUYYAWKBN1/eriddoch',
#           'Email': 'eric.riddoch@bengroup.com',
#           'ExternalLoginFederationProviderType': 'CUSTOM_OIDC',
#           'ExternalLoginFederationProviderUrl': 'https://cognito-idp.us-east-2.amazonaws.com/us-east-2_T5XqAEdE9',
#           'ExternalLoginId': 'bd62c1ae-02e3-4b69-9295-21bdb5724cb0',
#           'IdentityType': 'IAM',
#           'PrincipalId': 'federated/iam/AROARLNW6ZBFQSG5ZP565:eriddoch',
#           'Role': 'READER',
#           'UserName': 'cognito-stack-webidentityroleD0021FE2-1HDKUYYAWKBN1/eriddoch'}}


# embed_url_response = client.generate_embed_url_for_registered_user(
#     AwsAccountId=ACCOUNT_ID,
#     UserArn=example_response["User"]['Arn'],
#     SessionLifetimeInMinutes=15,
#     ExperienceConfiguration={
#         "QuickSightConsole": {"InitialPath": "/start/favorites"}
#     },
# )

# example_embed_url_response = {'EmbedUrl': 'https://us-east-1.quicksight.aws.amazon.com/embedding/c006e6bb64f741bc9081db5f20a53f73/start/favorites?code=AYABeIdGa85IFyNlEf7Mj58fEJ0AAAABAAdhd3Mta21zAEthcm46YXdzOmttczp1cy1lYXN0LTE6MjU5NDgwNDYyMTMyOmtleS81NGYwMjdiYy03MDJhLTQxY2YtYmViNS0xNDViOTExNzFkYzMAuAECAQB4EeOLgrUr51nsHbjCawUUKjOqEm284CNxqOjvtm6TGiwBLs4qRtaOI7-NCkZe4Wj05QAAAH4wfAYJKoZIhvcNAQcGoG8wbQIBADBoBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDF-HDn0j3E3nKfIPoAIBEIA7xmSwvHty9TxAj1rmyCnwnlX35ofVy0mrnrGgPISO5BRoIRKZFAAurYNVZU70EnDu39OstFo7rtO9NxoCAAAAAAwAABAAAAAAAAAAAAAAAAAAefF9A9gn2Wju3iASUJWwzf____8AAAABAAAAAAAAAAAAAAABAAAA5f3NnHkgigGvT8143MClOl4DH7SN5f286-EEqkggXdMHlqRX3sDIZiRWIfKBNigYLfxJRklbq9PhnLq_z1huo5BzvFaFPntOfaGz64randnpWV-VA40Zm69imo-vY9kjQe_ZzUHSL4MC9ZPFsXbFRFcEWr7ePE6CaeyesdAIlfy1Tynl1E2-2Jun0JUTpTIDpWwRC-qoY0Ignw0i5BrUBa-NQk9Z7PDDG_F3mR7VYiG03FxVP-ydexvk7LVxTPN9Rbhw0PHNa5Doo9hZjfhiR0QvKd8l6aN9Rcgtyo661myT_iNKJWVGqOczNhwQNloxzHA9e8GK&identityprovider=quicksight&isauthcode=true',
#  'RequestId': 'ea117526-f980-41f3-be19-c61eb3b4aaba',
#  'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
#                                       'content-length': '1022',
#                                       'content-type': 'application/json',
#                                       'date': 'Thu, 28 Jul 2022 08:10:03 GMT',
#                                       'x-amzn-requestid': 'ea117526-f980-41f3-be19-c61eb3b4aaba'},
#                       'HTTPStatusCode': 200,
#                       'RequestId': 'ea117526-f980-41f3-be19-c61eb3b4aaba',
#                       'RetryAttempts': 0},
#  'Status': 200}

# from pprint import pprint
# # pprint(response)
# pprint(embed_url_response)

# # this is the policy in the IAM role
# # {
# #     "Version": "2012-10-17",
# #     "Statement": [
# #         {
# #             "Action": "quicksight:GetDashboardEmbedUrl",
# #             "Resource": "*",
# #             "Effect": "Allow"
# #         }
# #     ]
# # }
                
                
                
                
# # # example assume role using a token                
# # client.assume_role_with_web_identity(
# #     DurationSeconds=3600,
# #     Policy='{"Version":"2012-10-17","Statement":[{"Sid":"Stmt1","Effect":"Allow","Action":"s3:ListAllMyBuckets","Resource":"*"}]}',
# #     ProviderId='www.amazon.com',
# #     RoleArn='arn:aws:iam::123456789012:role/FederatedWebIdentityRole',
# #     RoleSessionName='app1',
# #     WebIdentityToken='Atza%7CIQEBLjAsAhRFiXuWpUXuRvQ9PZL3GMFcYevydwIUFAHZwXZXXXXXXXXJnrulxKDHwy87oGKPznh0D6bEQZTSCzyoCtL_8S07pLpr0zMbn6w1lfVZKNTBdDansFBmtGnIsIapjI6xKR02Yc_2bQ8LZbUXSGm6Ry6_BG7PrtLZtj_dfCTj92xNGed-CrKqjG7nPBjNIL016GGvuS5gSvPRUxWES3VYfm1wl7WTI7jn-Pcb6M-buCgHhFOzTQxod27L9CqnOLio7N3gZAGpsp6n1-AJBOCJckcyXe2c6uD0srOJeZlKUm2eTDVMf8IehDVI0r1QOnTV6KzzAI3OY87Vd_cVMQ',
# # )
from contextlib import contextmanager
from functools import lru_cache
from pprint import pprint
from typing import Tuple
import boto3
from jose.jwt import get_unverified_claims
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

from mypy_boto3_cognito_idp.type_defs import SignUpResponseTypeDef, AdminInitiateAuthResponseTypeDef

@lru_cache
def get_cognito_idp_client(region_name: str) -> CognitoIdentityProviderClient:
    return boto3.client("cognito-idp", region_name=region_name)

@contextmanager
def jwt_id_token_claims(email: str, password: str, cognito_web_client_id: str, cognito_user_pool_id: str, user_pool_region: str) -> dict:
    # create a real confirmed user in the Cognito User Pool
    try:
        delete_cognito_user(user_pool_id=cognito_user_pool_id, email=email, user_pool_region=user_pool_region)
    except get_cognito_idp_client(region_name=user_pool_region).exceptions.UserNotFoundException as e:
        print("No user to delete")
    register_cognito_user(
        email=email,
        password=password,
        app_client_id=cognito_web_client_id,
        user_pool_region=user_pool_region,
    )
    confirm_user_email(user_pool_id=cognito_user_pool_id, username=email, user_pool_region=user_pool_region)
    jwt_access_token, jwt_id_token, jwt_refresh_token = sign_in_user(
        email=email,
        password=password,
        user_pool_id=cognito_user_pool_id,
        app_client_id=cognito_web_client_id,
        user_pool_region=user_pool_region,
    )

    yield get_unverified_claims(jwt_id_token)

    # clean up the user
    delete_cognito_user(user_pool_id=cognito_user_pool_id, email=email, user_pool_region=user_pool_region)


#########################################
# --- Helper functions for fixtures --- #
#########################################


def register_cognito_user(email: str, password: str, app_client_id: str, user_pool_region: str) -> SignUpResponseTypeDef:
    """
    Raises:
        ClientError: if the user can't be signed up; for example, the user
            may already exist or the app_client_id could be wrong
    """
    cognito_idp = get_cognito_idp_client(region_name=user_pool_region)
    # Add user to pool
    sign_up_response: SignUpResponseTypeDef = cognito_idp.sign_up(
        ClientId=app_client_id,
        Username=email,
        Password=password,
        UserAttributes=[{"Name": "email", "Value": email}],
    )

    return sign_up_response


def confirm_user_email(user_pool_id: str, username: str, user_pool_region: str) -> dict:
    """Confirm a user's email address. For rootski, the ``username`` is their email."""
    cognito_idp = get_cognito_idp_client(region_name=user_pool_region)
    print("    Confirming user...")
    # Use Admin powers to confirm user. Normally the user would
    # have to provide a code or click a link received by email
    confirm_sign_up_response = cognito_idp.admin_confirm_sign_up(UserPoolId=user_pool_id, Username=username)

    return confirm_sign_up_response


def sign_in_user(email: str, password: str, user_pool_id: str, app_client_id: str, user_pool_region: str) -> Tuple[str, str, str]:
    cognito_idp = get_cognito_idp_client(region_name=user_pool_region)

    # This is less secure, but simpler
    response: AdminInitiateAuthResponseTypeDef = cognito_idp.admin_initiate_auth(
        AuthFlow="ADMIN_NO_SRP_AUTH",
        AuthParameters={"USERNAME": email, "PASSWORD": password},
        UserPoolId=user_pool_id,
        ClientId=app_client_id,
    )

    print("----- Log in response -----")
    pprint(response)
    print("---------------------------")
    # AWS official docs on using tokens with user pools:
    # https://amzn.to/2HbmJG6
    # If authentication was successful we got three tokens
    jwt_access_token = response["AuthenticationResult"]["AccessToken"]
    jwt_id_token = response["AuthenticationResult"]["IdToken"]
    jwt_refresh_token = response["AuthenticationResult"]["RefreshToken"]

    return jwt_access_token, jwt_id_token, jwt_refresh_token


def delete_cognito_user(user_pool_id: str, email: str, user_pool_region: str):
    cognito_idp = get_cognito_idp_client(region_name=user_pool_region)
    cognito_idp.admin_delete_user(UserPoolId=user_pool_id, Username=email)
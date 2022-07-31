from typing import List, OrderedDict
from simple_salesforce import Salesforce, SFType

def fetch_all_salesforce_object_fields(username: str, password: str, security_token: str, obj_name: str):
    sf = Salesforce(
        username=username,
        password=password,
        security_token=security_token
    )

    sf_obj: SFType = getattr(sf, obj_name)
    obj_describe_result: OrderedDict = sf_obj.describe()
    field_odicts: List[OrderedDict] = obj_describe_result["fields"]
    fields: List[str] = list(field["name"] for field in field_odicts)

    # print(sf_fields_dict["fields"])

    return fields

def make_select_star_soql_stmt(obj_name: str, fields: List[str]) -> str:
    field_selector_stmt = ", ".join(fields)
    return f"SELECT {field_selector_stmt} FROM {obj_name}"

def create_select_star_soql_stmt(username: str, password: str, security_token: str, obj_name: str) -> str:
    fields: List[str] = fetch_all_salesforce_object_fields(
        username=username,
        password=password,
        security_token=security_token,
        obj_name=obj_name,
    )
    stmt: str = make_select_star_soql_stmt(
        fields=fields,
        obj_name=obj_name,
    )
    return stmt



username = "eric.russia97@gmail.com"
password = "Ozg0&WgLb6jTsg7"

# get this here: https://docs.idalko.com/exalate/display/ED/Salesforce%3A+How+to+generate+a+security+token
security_token = "lVqxLRwIFZsyVFLRYlT4FvSwf"

password_with_token = password + security_token

select_star_soql_stmt = create_select_star_soql_stmt(
    username=username,
    password=password,
    security_token=security_token,
    obj_name="account",
) 

print(select_star_soql_stmt)
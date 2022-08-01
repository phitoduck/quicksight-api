import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from dataclasses import dataclass

import boto3
import json

from typing import List, Optional, OrderedDict, Type
from simple_salesforce import Salesforce, SFType
import os
from pprint import pprint, pformat

AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")


#######################
# --- Dataclasses --- #
#######################

@dataclass
class JobArgs:
    """Object to easily access CLI arguments passed to the glue job."""
    
    ############################
    # --- Custom Arguments --- #
    ############################
    
    # bucket to write the output of this job to
    output_bucket_name: str
    # name of the customer the data is written for
    customer_org_name: str

    ###################################
    # --- Standard Glue Arguments --- #
    ###################################

    job_id: Optional[str]
    job_run_id: Optional[str]
    job_bookmark_from: Optional[str]
    job_bookmark_to: Optional[str]

    security_configuration: Optional[str]
    temp_dir: Optional[str]
    redshift_temp_dir: Optional[str]
    encryption_type: Optional[str]

    job_bookmark_option: str = "job-bookmark-disable"

    def __str__(self) -> str:
        return pformat(self.__dict__)


    @classmethod
    def parse_from_argv(cls: Type["JobArgs"]) -> "JobArgs":

        opts: dict = getResolvedOptions(
            args=sys.argv, 
            options=[
                "custom__output_bucket_name",
                "custom__customer_org_name",
            ],
        )

        print("\nALL ARGS PASSED TO JOB:")
        pprint(opts)
        print()

        return cls(
            output_bucket_name=opts["custom__output_bucket_name"],
            customer_org_name=opts["custom__customer_org_name"],

            job_id=opts["JOB_ID"],
            job_run_id=opts["JOB_RUN_ID"],
            job_bookmark_option=opts["job_bookmark_option"],
            job_bookmark_from=opts["job_bookmark_from"],
            job_bookmark_to=opts["job_bookmark_to"],
            security_configuration=opts["SECURITY_CONFIGURATION"],
            temp_dir=opts["TempDir"],
            redshift_temp_dir=opts["RedshiftTempDir"],
            encryption_type=opts["encryption_type"],
        )


@dataclass
class Credentials:
    username: str
    password: str
    security_token: str

    @property
    def password_with_security_tkn(self) -> str:
        return self.password + self.security_token

    @staticmethod
    def fetch_secret_by_id(secret_id: str):
        secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = secrets_client.get_secret_value(SecretId=secret_id)
        secret_json = response["SecretString"]
        secret = json.loads(secret_json)
        return secret

    @classmethod
    def from_secrets_manager(cls: Type["Credentials"], secret_id: str) -> "Credentials":
        secret: dict = Credentials.fetch_secret_by_id(secret_id)
        return cls(**secret)


@dataclass
class SFObjectField:
    """
    A utility class to help determine which salesforce fields are able to be
    sent to SOQL queries to the Bulk APIs.

    Information about individual fields comes from here:
    https://developer.salesforce.com/docs/atlas.en-us.234.0.object_reference.meta/object_reference/sforce_api_objects_account.htm
    """

    is_custom: bool
    name: str
    compound_field_name: Optional[str]
    type: str

    @classmethod
    def from_sf_odict(
        cls: Type["SFObjectField"], sf_odict: OrderedDict
    ) -> "SFObjectField":
        return cls(
            is_custom=sf_odict["custom"],
            name=sf_odict["name"],
            compound_field_name=sf_odict["compoundFieldName"],
            type=sf_odict["type"],
        )

    def is_compound_field(self) -> bool:
        """
        Compound fields cannot be queried via salesforce Bulk APIs.
        So, it's important to know whether it is compond to omit it in select statements.
        """
        field_is_a_location = self.type in ["address", "location"]
        field_has_a_compound_key = self.compound_field_name is not None
        is_compound = field_is_a_location or field_has_a_compound_key
        return is_compound

    # NOTE: specific to Account-object
    def requires_field_service_to_be_enabled(self) -> bool:
        """
        'Field Service' refers to when sales reps go onsite.
        In this case, operating hours of their customers is important to know.

        It's unlikely that most salesforce accounts will have this enabled,
        so we'll exclude it.
        """
        fields_requiring_field_service = ["OperatingHoursId".lower()]
        return self.name.lower() in fields_requiring_field_service

    def is_incompatible_with_bulk_apis(self) -> bool:
        return self.is_compound_field() or self.requires_field_service_to_be_enabled()


#####################
# --- Constants --- #
#####################

SF_CREDENTIALS = Credentials.from_secrets_manager(secret_id="sf-credentials")
JOB_ARGS = JobArgs.parse_from_argv()

print("\nParsed Job Args:")
print(JOB_ARGS)
print()


############################
# --- Helper Functions --- #
############################

# TODO: if we keep this, add an option to filter out compound fields
def fetch_all_standard_fields_on_sf_object(
    username: str, password: str, security_token: str, obj_name: str
):
    sf = Salesforce(username=username, password=password, security_token=security_token)

    response = sf.query(f"SELECT FIELDS(STANDARD) FROM {obj_name} LIMIT 1")
    record: OrderedDict = response["records"][0]

    fields = [k for k in record.keys()]

    return fields


def fetch_all_salesforce_object_fields(
    username: str, password: str, security_token: str, obj_name: str
):
    """
    An issue with fetching *all* fields is that the given user may not have "Field Level Security"
    access for a handful of the fields. This means that there are certain fields the
    user is not allowed to query--resulting in failed queries.
    """
    sf = Salesforce(username=username, password=password, security_token=security_token)

    sf_obj: SFType = getattr(sf, obj_name)
    obj_describe_result: OrderedDict = sf_obj.describe()
    field_odicts: List[OrderedDict] = obj_describe_result["fields"]

    def pprint_to_file(thing):
        from pprint import pprint
        from pathlib import Path

        THIS_DIR = Path(__file__).parent
        with open(THIS_DIR / "describe_account.txt", "wt") as file:
            pprint(thing, stream=file)

    field_objs: List[SFObjectField] = list(
        SFObjectField.from_sf_odict(o) for o in field_odicts
    )
    non_compound_field_objs = [
        obj for obj in field_objs if not obj.is_incompatible_with_bulk_apis()
    ]

    fields = [obj.name for obj in non_compound_field_objs]

    return fields


def make_select_star_soql_stmt(obj_name: str, fields: List[str]) -> str:
    field_selector_stmt = ", ".join(fields)
    return f"SELECT {field_selector_stmt} FROM {obj_name}"


def generate_select_star_soql_stmt(
    username: str, password: str, security_token: str, obj_name: str
) -> str:
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


#####################
# --- Spark Job --- #
#####################


def run(sf_credentials: Credentials):
    sc = SparkContext.getOrCreate()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)

    select_star_soql_stmt = generate_select_star_soql_stmt(
        username=sf_credentials.username,
        password=sf_credentials.password,
        security_token=sf_credentials.security_token,
        obj_name="account",
    )

    print("\Derived this query for 'SELECT *':")
    print(select_star_soql_stmt)

    print("\nExecuting the query...")
    df = (
        spark.read.format("com.springml.spark.salesforce")
        .option("username", sf_credentials.username)
        .option("password", sf_credentials.password_with_security_tkn)
        .option("soql", select_star_soql_stmt)
        .option("bulk", True)
        # Opportunity.LastStageChangeDate is only availaable in API v52
        .option("version", 52)
        .option("sfObject", "account")
        .load()
    )

    json_first_row = df.selectExpr("*").limit(1).toPandas().to_json(orient="records")
    print("\nFirst row:")
    pprint(json_first_row)

    print("\n df.head()")
    print(df.head())

    print("\ndf.show()")
    print(df.show())

    job.commit()


run(sf_credentials=SF_CREDENTIALS)

# print(df.show())


# select_star_soql_stmt = create_select_star_soql_stmt(
#     username=SF_CREDENTIALS.username,
#     password=SF_CREDENTIALS.password,
#     security_token=SF_CREDENTIALS.security_token,
#     obj_name="account",
# )

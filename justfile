# read environment variables from the .env file
set dotenv-load := true

# constants accessible with {{CONSTANT_NAME}} syntax
AWS_PROFILE := "ben-ai-sandbox"
AWS_REGION := "us-east-2"
GLUE_VOLUMES_DIR := "iac/resources/glue/volumes"


install:
    python -m pip install -e ./iac
    python -m pip install -r ./iac/resources/glue/fetch-maven.requirements.txt
    python -m pip install -e ./backend_api[dev]


######################
# --- Deployment --- #
######################

deploy-cdk: download-local-glue-dependencies
    cd ./iac/ \
        && cdk deploy --profile {{AWS_PROFILE}} --all --require-approval never

deploy-glue: download-local-glue-dependencies
    cd ./iac/ \
        && cdk deploy --profile {{AWS_PROFILE}} "quicksight-glue" --require-approval never

synth-glue: download-local-glue-dependencies
    cd ./iac/ \
        && cdk synth --profile {{AWS_PROFILE}} "quicksight-glue" --require-approval never

create-salesforce-credentials-secret:
    #!/bin/bash

    # Note: the .env file in this repo must contain these referenced values
    SECRET=`cat << EOF
    {
        "username": "$SF_USERNAME",
        "password": "$SF_PASSWORD",
        "security_token": "$SF_SECURITY_TOKEN"
    }
    EOF`

    echo "SECRET_YAML" | \
    aws secretsmanager create-secret \
        --name "sf-credentials" \
        --description "Salesforce API credentials for development account" \
        --profile {{AWS_PROFILE}} \
        --region {{AWS_REGION}} \
        --secret-string "$SECRET" | cat


##################################
# --- Teardown of Deployment --- #
##################################

delete-salesforce-credentials-secret:
    aws secretsmanager delete-secret \
        --secret-id "sf-credentials" \
        --force-delete-without-recovery \
        --profile {{AWS_PROFILE}} \
        --region {{AWS_REGION}} | cat

# Note: this may fail due certain AWS resources requiring manual deletion.
#  For example, S3 buckets usually cannot be deleted if they have objects in them.
cdk-destroy: delete-salesforce-credentials-secret
    cd ./iac/ \
        && cdk destroy --profile {{AWS_PROFILE}} --all --require-approval never


##################################
# --- Local Glue Development --- #
##################################

download-local-glue-dependencies: glue-download-jars glue-download-python-deps

glue-download-jars:
    mkdir -p {{GLUE_VOLUMES_DIR}}/maven_jars
    {{ path_exists( "iac/resources/glue/volumes/maven_jars/force-partner-api-40.0.0.jar" ) }} || \
        python iac/resources/glue/fetch_maven_jars.py

glue-download-python-deps:
    mkdir -p {{GLUE_VOLUMES_DIR}}/python-packages
    {{ path_exists( "iac/resources/glue/volumes/python-packages/simple_salesforce" ) }} || \
        ( \
            mkdir -p {{GLUE_VOLUMES_DIR}}/python-packages && \
            docker run --rm \
                --entrypoint python \
                -v $PWD/{{GLUE_VOLUMES_DIR}}/python-packages:/packages \
                python:3.7-slim-buster \
                    -m pip install simple-salesforce -t /packages \
        )

glue-start-jupyter: download-local-glue-dependencies
    cd ./iac/resources/glue && docker-compose up


##########################
# --- Static Website --- #
##########################

invalidate-s3-cache: 
	python ./iac/aws_invalidate_stack.py \
		--s3-static-site-stack-name "quicksight-static-site" \
		--region {{AWS_REGION}} \
		--profile {{AWS_PROFILE}}

# after running 'make html' or 'make docs-docker', run this to
# upload the docs to S3 and incalidate the CloudFront cache so that
# users can access the new in the browser
publish-to-s3: invalidate-s3-cache
	aws s3 sync ./src/quicksight_poc/static/ s3://quicksight.ben-ai-sandbox.com/ --acl public-read --profile {{AWS_PROFILE}}


############################
# --- Project Template --- #
############################

update-pyscaffold:
    #!/bin/bash

    REPO_HAS_UNCOMMITTED_CHANGES=$(git diff --quiet || echo "yes" && "no")

    if [[ "$REPO_HAS_UNCOMMITTED_CHANGES" == "yes" ]]
    then
        echo "You have uncommitted changes. This target may overwrite them"
        echo "and cause you to lose your work! Enter "y" if you don't care"
        echo "and would like to proceed."
        read -p "(y/n) " RESPONSE
        
        if [[ "$RESPONSE" != "y" ]]
        then
            echo "Aborted."
            exit 0
        fi
    fi

    echo "Updating pyscaffold..."

    which pipx || python -m pip install pipx
    python -m pipx run \
        --spec /Users/eric/repos/extra/playwith-pyscaffold/pyscaffoldext-eric-extension \
        --editable \
            putup . --update --force

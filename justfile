set dotenv-load := true

AWS_PROFILE := "ben-ai-sandbox"

download-local-glue-dependencies:
    cd ./iac/resources/glue

    {{ path_exists( "iac/resources/glue/volumes/maven_jars/force-partner-api-40.0.0.jar" ) }} || \
        python iac/resources/glue/fetch_maven_jars.py

    {{ path_exists( "iac/resources/glue/volumes/python-packages/simple_salesforce" ) }} || \
        docker run --rm \
            --entrypoint python \
            -v $PWD/volumes/python-packages:/packages \
            python:3.7-slim-buster \
                -m pip install simple-salesforce -t /packages  


install:
    python -m pip install -e ./iac
    python -m pip install -r ./iac/resources/glue/fetch-maven.requirements.txt
    python -m pip install -e ./backend_api[dev]


glue-start-jupyter: download-local-glue-dependencies
    cd ./iac/resources/glue
    docker-compose up


invalidate-s3-cache:
	python ./iac/aws_invalidate_stack.py \
		--s3-static-site-stack-name "quicksight-static-site" \
		--region "us-east-2" \
		--profile {{AWS_PROFILE}}

# NOTE: quicksight-glue requires the maven jars to be present in this project
deploy-cdk:
    cd ./iac/ \
        && cdk deploy --profile {{AWS_PROFILE}} --all --require-approval never

# NOTE: quicksight-glue requires the maven jars to be present in this project
deploy-glue:
    cd ./iac/ \
        && cdk deploy --profile {{AWS_PROFILE}} "quicksight-glue" --require-approval never

# after running 'make html' or 'make docs-docker', run this to
# upload the docs to S3 and incalidate the CloudFront cache so that
# users can access the new in the browser
publish-to-s3: invalidate-s3-cache
	aws s3 sync ./src/quicksight_poc/static/ s3://quicksight.ben-ai-sandbox.com/ --acl public-read --profile {{AWS_PROFILE}}

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

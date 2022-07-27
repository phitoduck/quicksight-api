install:
    python -m pip install -e .[dev]

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

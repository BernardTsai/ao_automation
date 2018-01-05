#!/bin/bash

# ----- ensure the environment variables are set correctly ---------------------

echo Validating parameters

if [ -z "$PROJECT" ]; then
    echo "Environment variable PROJECT is undefined"
    exit 1
fi

if [ -z "$LOCATION" ]; then
    echo "Environment variable LOCATION is undefined"
    exit 1
fi

if [ -z "$CONTENT" ]; then
    echo "Environment variable CONTENT is undefined"
    exit 1
fi

export TOKEN=gitlab_token

# ----- determine project id ---------------------------------------------------

echo Determine project

export APPLICATION=$(echo "$PROJECT" | sed 's/\//%2F/g')
export HEADER="Private-Token: $TOKEN"
export PROJECTINFO=$(curl -s -H "$HEADER" "http://gitlab/api/v4/projects/$APPLICATION")
export PROJECTID=$( echo $PROJECTINFO | python -c "import sys, json; print( json.load(sys.stdin)['id'] )" )

echo $PROJECTID

# ----- upload inventory file --------------------------------------------------

echo Upload inventory

export FILE_PATH=$(echo "$LOCATION" | sed 's/\//%2F/g')
export HEADER="Private-Token: $TOKEN"
export DATA1="content=$CONTENT"
export DATA2="commit_message=inventory"
export DATA3="branch=master"
export RESULT=$(curl -s -d "$DATA1" -d "$DATA2" -d "$DATA3" -H "$HEADER" http://gitlab/api/v4/projects/$PROJECTID/repository/files/$FILE_PATH )

echo $RESULT
echo http://gitlab/api/v4/projects/$PROJECTID/repository/files/$FILE_PATH

# ----- finished ---------------------------------------------------------------

echo Cleanup completed

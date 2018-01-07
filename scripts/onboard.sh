#!/bin/bash

# ----- ensure the environment variables are set correctly ---------------------

echo Validating parameters

if [ -z "$TOKEN" ]; then
    echo "Environment variable TOKEN is undefined"
    exit 1
fi

if [ -z "$VNF" ]; then
    echo "Environment variable VNF is undefined"
    exit 1
fi

if [ -z "$UUID" ]; then
    echo "Environment variable UUID is undefined"
    exit 1
fi

# ----- prepare temporary directory --------------------------------------------

mkdir /tmp/$UUID
mkdir /tmp/$UUID/clusters

# ----- load descriptor --------------------------------------------------------

curl "http://gitlab/Applications/$VNF/raw/master/vnfd.yml" > /tmp/$UUID/vnfd.yaml

# ----- generating files -------------------------------------------------------

cat /tmp/$UUID/vnfd.yaml | generator -t playbook_parameters > /tmp/$UUID/playbook_parameters.yml
cat /tmp/$UUID/vnfd.yaml | generator -t cluster_parameters  | splitter -p > /tmp/$UUID/clusters

# ----- determine project ------------------------------------------------------

echo Determine project

export HEADER="Private-Token: $TOKEN"
export PROJECTINFO=$(curl -s -H "$HEADER" "http://gitlab/api/v4/projects/Applications%2F$VNF")
export PROJECTID=$( echo $PROJECTINFO | python -c "import sys, json; print( json.load(sys.stdin)['id'] )" )

echo $PROJECTID

# ----- upload files -----------------------------------------------------------

echo Upload files

upload_file() {
  export CONTENT=$(cat $1)
  export LOCATION=$2

  echo $LOCATION

  export FILE_PATH=$(echo "$LOCATION" | sed 's/\//%2F/g')
  export HEADER="Private-Token: $TOKEN"
  export DATA1="content=$CONTENT"
  export DATA2="commit_message=inventory"
  export DATA3="branch=master"
  export RESULT=$(curl -s -d "$DATA1" -d "$DATA2" -d "$DATA3" -H "$HEADER" http://gitlab/api/v4/projects/$PROJECTID/repository/files/$FILE_PATH )

  echo $RESULT
}

upload_file /tmp/$UUID/playbook_parameters.yml playbook_parameters.yml

# loop over all files in clusters directory
for filename in /tmp/$UUID/clusters/*.yml
do
  # determine filename as such
  name=${filename##*/}
  upload_file $filename clusters/$name
done

# ----- cleanup files ----------------------------------------------------------

rm -rf /tmp/$UUID

# ----- finished ---------------------------------------------------------------

echo Onboarding completed

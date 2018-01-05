#!/bin/bash

# ----- ensure the environment variables are set correctly ---------------------

echo Validating parameters

if [ -z "$OS_AUTH_URL" ]; then
    echo "Environment variable OS_AUTH_URL is undefined"
    exit 1
fi

if [ -z "$OS_USERNAME" ]; then
    echo "Environment variable OS_USERNAME is undefined"
    exit 1
fi

if [ -z "$OS_PASSWORD" ]; then
    echo "Environment variable OS_PASSWORD is undefined"
    exit 1
fi

if [ -z "$OS_PROJECT_NAME" ]; then
    echo "Environment variable OS_PROJECT_NAME is undefined"
    exit 1
fi

# ----- check that we are not by chance deleting a critical project ------------

echo Checking project name

if [[ "$OS_PROJECT_NAME" =~ ^(admin|service)$ ]]; then
    echo "Cleanup script should not destroy system tenants"
    exit 2
fi

# ----- check availability of CLI client ---------------------------------------

echo Checking CLI client

type openstack > /dev/null 2>&1

if [ "$?" != "0" ]; then
  echo "OpenStack CLI Client has not been installed"
  exit 3
fi

# ----- check connectivity and access privileges to API endpoint ---------------

echo Checking API access

openstack user show $OS_USERNAME > /dev/null

if [ "$?" != "0" ]; then
  echo "Unable to access the API endpoint"
  exit 4
fi

# ----- detach all volumes -----------------------------------------------------

echo Detaching volumes

volume_ids="$(openstack volume list --project $OS_PROJECT_NAME | awk '{print $2}' | tail -n +4)"
for volume_id in "${volume_ids[@]}"
do
  if [ "$volume_id" != "" ]
  then
    server_ids=$(openstack volume show "$volume_id" -f json | jq -r ".attachments[].server_id")
    for server_id in "${server_ids[@]}"
    do
      if [ "$server_id" != "" ]
      then
        openstack server remove volume $server_id $volume_id
      fi
    done
  fi
done

# ----- delete all volumes -----------------------------------------------------

echo Deleting volumes

openstack volume list --project $OS_PROJECT_NAME | awk '{print $2}' | tail -n +4 | xargs openstack volume delete

# ----- delete all servers -----------------------------------------------------

echo Deleting servers

openstack server list | awk '{print $2}' | tail -n +4 | xargs openstack server delete

# ----- delete all ports -------------------------------------------------------

echo Deleting ports

openstack port list --project $OS_PROJECT_NAME | awk '{print $2}' | tail -n +4 | xargs openstack port delete

# ----- delete all networks ----------------------------------------------------

echo Deleting networks

openstack network list --no-share --project $OS_PROJECT_NAME | awk '{print $2}' | tail -n +4 | xargs openstack network delete

# ----- delete all security groups ---------------------------------------------

echo Deleting security groups

openstack security group list --project $OS_PROJECT_NAME | awk '$4 != "default"'| awk '{print $2}' | tail -n +4 | xargs openstack security group delete

# ----- delete all keys --------------------------------------------------------

echo Deleting keys

openstack keypair list | awk '{print $2}' | tail -n +4 | xargs openstack keypair delete

# ----- finished ---------------------------------------------------------------

echo Cleanup completed

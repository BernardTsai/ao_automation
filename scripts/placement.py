#!/usr/bin/env python

import shade
import sys
import os
import os_client_config

# ------------------------------------------------------------------------------

def main():
    # get environment variables
    cloud_name   = os.environ['OS_CLOUD']
    vnf_name     = os.environ['OS_VNF_NAME']
    project_name = os.environ['OS_PROJECT_NAME']
    cluster_name = os.environ['OS_CLUSTER_NAME']

    # Context: central administration
    try:
        cloud_config = os_client_config.OpenStackConfig().get_one_cloud( cloud_name )

        cloud = shade.OpenStackCloud(cloud_config=cloud_config)
    except Exception as exc:
        print(exc)
        sys.exit(1)

    # Get servers
    data = cloud.list_servers(detailed=False)

    # dictionary of all found servers
    nodes = {}

    # filter servers
    cluster_prefix = vnf_name + "_" + project_name + "_" + cluster_name
    for entity in data:
        name = entity["name"]
        if name.startswith(cluster_prefix):
            # index is the last substring after the last "_" seperator
            index = name.split("_")[-1]

            # availability zone
            zone = entity["location"].zone

            nodes[index] = {"zone": zone}

    # find next available slot
    index = 0
    while str(index) in nodes.keys():
        index = index + 1

    print("{'node':'" + str(index) + "'}")

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

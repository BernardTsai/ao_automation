#!/usr/bin/env python

import shade
import yaml
import sys
import os
import os_client_config

# ------------------------------------------------------------------------------

# data
cloud_name      = None
project_name    = None
password        = None

tenant          = None
security_groups = None
networks        = None
subnets         = None
ports           = None
nodes           = None
servers         = None

# ------------------------------------------------------------------------------

class Tenant():
    def __init__(self, data):
        global password
        global cloud_name
        
        self.id          = data["id"]
        self.name        = data["name"]
        self.description = data["description"]
        self.password    = password
        self.cloud       = cloud_name

# ------------------------------------------------------------------------------

class SecurityGroupRule():
    def __init__(self, data):
        self.id          = data["id"]
        self.type        = data["ethertype"]
        self.direction   = data["direction"]
        self.protocol    = data["protocol"]
        self.min         = data["port_range_min"]
        self.max         = data["port_range_max"]
        self.group       = data["remote_group_id"]
        self.prefix      = data["remote_ip_prefix"]

# ------------------------------------------------------------------------------

class SecurityGroup():
    def __init__(self, data):
        self.id          = data["id"]
        self.name        = data["name"]
        self.description = data["description"]
        self.rules       = []

        for entity in data["security_group_rules"]:
            rule = SecurityGroupRule(entity)
            self.rules.append(rule)

# ------------------------------------------------------------------------------

class SecurityGroups():
    def __init__(self, data):
        self.groups = {}

        for entity in data:
            group = SecurityGroup(entity)
            self.groups[group.id] = group

        for group in self.groups.values():
            for rule in group.rules:
                if rule.group:
                    remote_group = self.groups[rule.group]

                    rule.group = remote_group.name

# ------------------------------------------------------------------------------

class Network():
    def __init__(self, data):
        self.id   = data["id"]
        self.name = data["name"]
        self.ipv4 = None
        self.ipv6 = None

# ------------------------------------------------------------------------------

class Networks():
    def __init__(self, data):
        self.networks = {}

        for entity in data:
            if not entity["shared"] == "False":
                network = Network(entity)
                self.networks[network.id] = network

# ------------------------------------------------------------------------------

class Subnet():
    def __init__(self, data):
        self.id      = data["id"]
        self.name    = data["name"]
        self.cidr    = data["cidr"]
        self.type    = str(data["ip_version"])
        self.network = data["network_id"]


# ------------------------------------------------------------------------------

class Subnets():
    def __init__(self, networks, data):
        for entity in data:
            subnet = Subnet(entity)

            # check if network can be found
            network = networks.networks[subnet.network]
            # add subnet to network
            if subnet.type == "4":
                network.ipv4 = subnet
            if subnet.type == "6":
                network.ipv6 = subnet

# ------------------------------------------------------------------------------

class Port():
    def __init__(self, data):
        self.id      = data["id"]
        self.name    = data["name"]
        self.device  = data["device_id"]
        self.network = data["network_id"]
        self.group   = None

        if data["security_groups"]:
            self.group = data["security_groups"][0]

# ------------------------------------------------------------------------------

class Ports():
    def __init__(self, data):
        self.ports = {}

        for entity in data:
            port = Port(entity)
            self.ports[port.id] = port

# ------------------------------------------------------------------------------

class Node():
    def __init__(self, data):
        # print(data.addresses)
        self.id                = data["id"]
        self.name              = data["name"]
        self.availability_zone = data["location"].zone
        self.flavor            = data["flavor"].name
        self.image             = data["image"].name
        self.key_name          = data["key_name"]
        self.nics              = []

        for address in data.addresses.keys():
            self.nics.append(address)

# ------------------------------------------------------------------------------

class Nodes():
    def __init__(self, data):
        self.nodes = {}

        for entity in data:
            node = Node(entity)
            self.nodes[node.id] = node

# ------------------------------------------------------------------------------

class Volume():
    def __init__(self, data):
        global nodes

        self.id     = data["id"]
        self.name   = data["name"]
        self.size   = data["size"]
        self.type   = data["volume_type"]
        self.server = None
        self.device = None

        if data["attachments"]:
            attachment = data["attachments"][0]
            self.server = nodes.nodes[attachment["server_id"]].name
            self.device = attachment["device"]

# ------------------------------------------------------------------------------

class Volumes():
    def __init__(self, data):
        self.volumes = {}

        for entity in data:
            volume = Volume(entity)
            self.volumes[volume.id] = volume

# ------------------------------------------------------------------------------

def main():
    global nodes
    global password
    global cloud_name
    global project_name

    # get environment variables
    password     = os.environ['OS_PASSWORD']
    cloud_name   = os.environ['OS_CLOUD']
    vnf_name     = os.environ['OS_VNF_NAME']
    project_name = os.environ['OS_PROJECT_NAME']

    # Context: central administration
    try:
        cloud_config = os_client_config.OpenStackConfig().get_one_cloud( cloud_name )

        cloud = shade.OpenStackCloud(cloud_config=cloud_config)
    except Exception as exc:
        print(exc)
        sys.exit(1)

    # Get project
    data   = cloud.get_project(vnf_name + "_" + project_name)

    tenant = Tenant(data)

    # Context: tenant administration
    try:
        cloud_config = os_client_config.OpenStackConfig().get_one_cloud( vnf_name + "_" + project_name )

        cloud = shade.OpenStackCloud(cloud_config=cloud_config)
    except Exception as exc:
        print(exc)
        sys.exit(1)

    # # Get flavors
    # data = cloud.list_flavors()

    # flavors = Flavors(data)

    # Get security groups
    data    = cloud.list_security_groups()

    security_groups = SecurityGroups(data)

    # Get networks
    data = cloud.list_networks()

    networks = Networks(data)

    # Get subnets
    data = cloud.list_subnets()

    subnets = Subnets(networks,data)

    # Get servers
    data = cloud.list_servers(detailed=True)

    nodes = Nodes(data)

    # Get ports
    # filters = { "tenant_id": tenant.id }
    data = cloud.list_ports()

    ports = Ports(data)

    # Get volumes
    # filters = { "tenant_id": tenant.id }
    data = cloud.list_volumes()

    volumes = Volumes(data)

    # ----- ouput data ---------------------------------------------------------

    print("---")
    print("tenant:")
    print("  name:        {}".format(tenant.name))
    print("  description: {}".format(tenant.description))
    print("  password:    {}".format(tenant.password))
    print("  cloud:       {}".format(tenant.cloud))
    print()

    print("security_groups:")
    for group_id, group in security_groups.groups.items():
        print("- {}".format(group.name))
    print()

    print("external_security_group_rules:")
    for group_id, group in security_groups.groups.items():
        for rule in group.rules:
            if rule.prefix:
                print("- group:            {}".format( group.name ) )
                print("  direction:        {}".format( rule.direction ) )
                print("  ethertype:        {}".format( rule.type ) )
                print("  protocol:         {}".format( rule.protocol ) )
                print("  min:              {}".format( rule.min ) )
                print("  max:              {}".format( rule.max ) )
                print("  mode:             {}".format( "cidr" ) )
                print("  remote_ip_prefix: {}".format( rule.prefix ) )
    print()

    print("internal_security_group_rules:")
    for group_id, group in security_groups.groups.items():
        for rule in group.rules:
            if rule.group:
                print("- group:            {}".format( group.name ) )
                print("  direction:        {}".format( rule.direction ) )
                print("  ethertype:        {}".format( rule.type ) )
                print("  protocol:         {}".format( rule.protocol ) )
                print("  min:              {}".format( rule.min ) )
                print("  max:              {}".format( rule.max ) )
                print("  mode:             {}".format( "group" ) )
                print("  remote_group:     {}".format( rule.group ) )
    print()

    print("networks:")
    for network_id, network in networks.networks.items():
        print("- name: {}".format( network.name ) )
        if network.ipv4:
            print("  ipv4:")
            print("    cidr: {}".format(network.ipv4.cidr))
        if network.ipv6:
            print("  ipv6:")
            print("    cidr: {}".format(network.ipv6.cidr))
    print()

    print("nodes:")
    for node_id, node in nodes.nodes.items():
        print("- name:              {}".format(node.name))
        print("  availability_zone: {}".format(node.availability_zone))
        print("  flavor:            {}".format(node.flavor))
        print("  image:             {}".format(node.image))
        print("  key_name:          {}".format(node.key_name))
        if not node.nics:
            print("  nics: []")
        else:
            print("  nics:")
            for nic in node.nics:
                print("  - port-name: {}".format(nic))
    print()

    print("volumes:")
    for volume_id, volume in volumes.volumes.items():
        print("- name:   {}".format(volume.name))
        print("  server: {}".format(volume.server))
        print("  type:   {}".format(volume.type))
        print("  size:   {}".format(volume.size))
        print("  device: {}".format(volume.device))
    print()
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

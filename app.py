#!/usr/bin/env python3
import aws_cdk as cdk
from cap_stone_vpc_p.vpc_stack import CapStoneVpcStack
from cap_stone_vpc_p.transit_gateway_stack import TransitGatewayStack
from cap_stone_vpc_p.peering_stacks import USEUPeeringStack, USAPPeeringStack, EUAPPeeringStack
from cap_stone_vpc_p.vpn_stack import VpnStack

app = cdk.App()

# VPC stacks
us_east_vpc = CapStoneVpcStack(app, "CapStoneVpc-us-east-1",
    env=cdk.Environment(region="us-east-1"),
    vpc_cidr="172.16.0.0/16",
    region="us-east-1"
)

eu_west_vpc = CapStoneVpcStack(app, "CapStoneVpc-eu-west-1",
    env=cdk.Environment(region="eu-west-1"),
    vpc_cidr="172.17.0.0/16",
    region="eu-west-1"
)

ap_southeast_vpc = CapStoneVpcStack(app, "CapStoneVpc-ap-southeast-1",
    env=cdk.Environment(region="ap-southeast-1"),
    vpc_cidr="172.18.0.0/16",
    region="ap-southeast-1"
)

# Transit Gateway stacks
us_east_tgw = TransitGatewayStack(app, "TransitGatewayStack-us-east-1",
    env=cdk.Environment(region="us-east-1"),
    vpcs=[{"vpc": us_east_vpc.vpc, "region": "us-east-1", "cidr": "172.16.0.0/16", "private_subnet_ids": us_east_vpc.private_subnet_ids}]
)
us_east_tgw.add_dependency(us_east_vpc)

eu_west_tgw = TransitGatewayStack(app, "TransitGatewayStack-eu-west-1",
    env=cdk.Environment(region="eu-west-1"),
    vpcs=[{"vpc": eu_west_vpc.vpc, "region": "eu-west-1", "cidr": "172.17.0.0/16", "private_subnet_ids": eu_west_vpc.private_subnet_ids}]
)
eu_west_tgw.add_dependency(eu_west_vpc)

ap_southeast_tgw = TransitGatewayStack(app, "TransitGatewayStack-ap-southeast-1",
    env=cdk.Environment(region="ap-southeast-1"),
    vpcs=[{"vpc": ap_southeast_vpc.vpc, "region": "ap-southeast-1", "cidr": "172.18.0.0/16", "private_subnet_ids": ap_southeast_vpc.private_subnet_ids}]
)
ap_southeast_tgw.add_dependency(ap_southeast_vpc)

# Peering stacks
us_eu_peering = USEUPeeringStack(app, "USEUPeeringStackV5",
    env=cdk.Environment(region="us-east-1"),
    us_tgw_id=us_east_tgw.transit_gateway_id,
    eu_tgw_id=eu_west_tgw.transit_gateway_id
)
us_eu_peering.add_dependency(us_east_tgw)
us_eu_peering.add_dependency(eu_west_tgw)

us_ap_peering = USAPPeeringStack(app, "USAPPeeringStackV5",
    env=cdk.Environment(region="us-east-1"),
    us_tgw_id=us_east_tgw.transit_gateway_id,
    ap_tgw_id=ap_southeast_tgw.transit_gateway_id
)
us_ap_peering.add_dependency(us_east_tgw)
us_ap_peering.add_dependency(ap_southeast_tgw)

eu_ap_peering = EUAPPeeringStack(app, "EUAPPeeringStackV5",
    env=cdk.Environment(region="eu-west-1"),
    eu_tgw_id=eu_west_tgw.transit_gateway_id,
    ap_tgw_id=ap_southeast_tgw.transit_gateway_id
)
eu_ap_peering.add_dependency(eu_west_tgw)
eu_ap_peering.add_dependency(ap_southeast_tgw)

# VPN stacks with company CIDR - Update company_cidr with your actual range
#company_cidr = "10.0.0.0/8"  # Replace with your company's CIDR

# us_east_vpn = VpnStack(app, "VpnStack-us-east-1",
#     env=cdk.Environment(region="us-east-1"),
#     vpc=us_east_vpc.vpc,
#     transit_gateway_id=us_east_tgw.transit_gateway_id,
#     company_cidr=company_cidr
# )
# us_east_vpn.add_dependency(us_east_tgw)

# eu_west_vpn = VpnStack(app, "VpnStack-eu-west-1",
#     env=cdk.Environment(region="eu-west-1"),
#     vpc=eu_west_vpc.vpc,
#     transit_gateway_id=eu_west_tgw.transit_gateway_id,
#     company_cidr=company_cidr
# )
# eu_west_vpn.add_dependency(eu_west_tgw)

# ap_southeast_vpn = VpnStack(app, "VpnStack-ap-southeast-1",
#     env=cdk.Environment(region="ap-southeast-1"),
#     vpc=ap_southeast_vpc.vpc,
#     transit_gateway_id=ap_southeast_tgw.transit_gateway_id,
#     company_cidr=company_cidr
# )
# ap_southeast_vpn.add_dependency(ap_southeast_tgw)

app.synth()
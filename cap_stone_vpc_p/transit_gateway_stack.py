from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from typing import List, Dict, Any

class TransitGatewayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpcs: List[Dict[str, Any]], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tgw = ec2.CfnTransitGateway(self, "TransitGateway",
            amazon_side_asn=64512,
            auto_accept_shared_attachments="enable",
            default_route_table_association="disable",
            default_route_table_propagation="disable",
            multicast_support="enable",
            description="Transit Gateway connecting multiple regions with multicast support",
            tags=[{"key": "Name", "value": "Multi-Region-TGW-Multicast"}]
        )

        tgw_route_table = ec2.CfnTransitGatewayRouteTable(self, "TGWRouteTable",
            transit_gateway_id=tgw.ref,
            tags=[{"key": "Name", "value": "TGW-Route-Table"}]
        )

        attachments = []
        for i, vpc_info in enumerate(vpcs):
            attachment = ec2.CfnTransitGatewayAttachment(self, f"TGWAttachment-{vpc_info['region']}",
                transit_gateway_id=tgw.ref,
                vpc_id=vpc_info["vpc"].vpc_id,
                subnet_ids=vpc_info["private_subnet_ids"],
                tags=[{"key": "Name", "value": f"TGW-Attachment-{vpc_info['region']}"}]
            )

            ec2.CfnTransitGatewayRouteTableAssociation(self, f"TGWRouteTableAssociation-{vpc_info['region']}",
                transit_gateway_attachment_id=attachment.ref,
                transit_gateway_route_table_id=tgw_route_table.ref
            )

            ec2.CfnTransitGatewayRouteTablePropagation(self, f"TGWRouteTablePropagation-{vpc_info['region']}",
                transit_gateway_attachment_id=attachment.ref,
                transit_gateway_route_table_id=tgw_route_table.ref
            )

            for subnet_idx, subnet_id in enumerate(vpc_info["private_subnet_ids"]):
                for other_vpc in vpcs:
                    if other_vpc["cidr"] != vpc_info["cidr"]:
                        ec2.CfnRoute(self, f"TGWRoute-{vpc_info['region']}-to-{other_vpc['region']}-{subnet_idx}",
                            route_table_id=vpc_info["vpc"].private_subnets[subnet_idx].route_table.route_table_id,
                            destination_cidr_block=other_vpc["cidr"],
                            transit_gateway_id=tgw.ref
                        )

            for subnet_idx, subnet in enumerate(vpc_info["vpc"].public_subnets):
                for other_vpc in vpcs:
                    if other_vpc["cidr"] != vpc_info["cidr"]:
                        ec2.CfnRoute(self, f"PublicTGWRoute-{vpc_info['region']}-to-{other_vpc['region']}-{subnet_idx}",
                            route_table_id=subnet.route_table.route_table_id,
                            destination_cidr_block=other_vpc["cidr"],
                            transit_gateway_id=tgw.ref
                        )

            attachments.append(attachment)

        multicast_domain = ec2.CfnTransitGatewayMulticastDomain(self, "MulticastDomain",
            transit_gateway_id=tgw.ref,
            options={"AutoAcceptSharedAssociations": "enable", "Igmpv2Support": "enable"},
            tags=[{"key": "Name", "value": "TGW-Multicast-Domain"}]
        )

        for i, vpc_info in enumerate(vpcs):
            for subnet_idx, subnet_id in enumerate(vpc_info["private_subnet_ids"]):
                ec2.CfnTransitGatewayMulticastDomainAssociation(self, f"MulticastAssociation-{vpc_info['region']}-{subnet_idx}",
                    transit_gateway_multicast_domain_id=multicast_domain.ref,
                    transit_gateway_attachment_id=attachments[i].ref,
                    subnet_id=subnet_id
                )

        self.transit_gateway_id = tgw.ref
        self.transit_gateway = tgw
        self.route_table = tgw_route_table

        CfnOutput(self, "TransitGatewayId", value=tgw.ref, export_name=f"{self.stack_name}-TransitGatewayId")
        CfnOutput(self, "TransitGatewayRouteTableId", value=tgw_route_table.ref, export_name=f"{self.stack_name}-RouteTableId")
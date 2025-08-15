from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class VpnStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, transit_gateway_id: str, company_cidr: str = "10.0.0.0/8", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Customer Gateway 
        customer_gateway = ec2.CfnCustomerGateway(self, "CustomerGateway",
            bgp_asn=65000,
            ip_address="0.0.0.0",  # Placeholder 
            type="ipsec.1",
            tags=[{"key": "Name", "value": f"CustomerGW-{self.region}"}]
        )

        # Create VPN Gateway
        vpn_gateway = ec2.CfnVpnGateway(self, "VpnGateway",
            type="ipsec.1",
            tags=[{"key": "Name", "value": f"VpnGW-{self.region}"}]
        )

        # Attach VPN Gateway to VPC
        ec2.CfnVPCGatewayAttachment(self, "VpnGatewayAttachment",
            vpc_id=vpc.vpc_id,
            vpn_gateway_id=vpn_gateway.ref
        )

        # Create VPN Connection
        vpn_connection = ec2.CfnVPNConnection(self, "VpnConnection",
            type="ipsec.1",
            customer_gateway_id=customer_gateway.ref,
            vpn_gateway_id=vpn_gateway.ref,
            static_routes_only=True,
            tags=[{"key": "Name", "value": f"VPN-{self.region}"}]
        )

        # Add static route
        ec2.CfnVPNConnectionRoute(self, "CompanyRoute",
            vpn_connection_id=vpn_connection.ref,
            destination_cidr_block=company_cidr
        )

        # Create Transit Gateway VPN Attachment
        tgw_vpn_attachment = ec2.CfnTransitGatewayVpnAttachment(self, "TgwVpnAttachment",
            transit_gateway_id=transit_gateway_id,
            vpn_connection_id=vpn_connection.ref,
            tags=[{"key": "Name", "value": f"TGW-VPN-Attachment-{self.region}"}]
        )

        # Add route to VPC route tables 
        for subnet in vpc.private_subnets:
            ec2.CfnRoute(self, f"CompanyRoute-{subnet.node.id}",
                route_table_id=subnet.route_table.route_table_id,
                destination_cidr_block=company_cidr,
                vpn_gateway_id=vpn_gateway.ref
            )

        # Outputs
        CfnOutput(self, "VpnGatewayId", value=vpn_gateway.ref, export_name=f"{self.stack_name}-VpnGatewayId")
        CfnOutput(self, "VpnConnectionId", value=vpn_connection.ref, export_name=f"{self.stack_name}-VpnConnectionId")
        CfnOutput(self, "CustomerGatewayId", value=customer_gateway.ref, export_name=f"{self.stack_name}-CustomerGatewayId")
        CfnOutput(self, "TgwVpnAttachmentId", value=tgw_vpn_attachment.ref, export_name=f"{self.stack_name}-TgwVpnAttachmentId")
        CfnOutput(self, "CompanyCidr", value=company_cidr, export_name=f"{self.stack_name}-CompanyCidr")
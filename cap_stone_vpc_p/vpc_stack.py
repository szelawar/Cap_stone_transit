from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class CapStoneVpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc_cidr: str, region: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "MyVPC",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(cidr_mask=24, name="Public", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(cidr_mask=24, name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ]
        )

        self.private_subnet_ids = self.vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids

        cross_region_sg = ec2.SecurityGroup(self, "CrossRegionSG",
            vpc=self.vpc,
            description="Security group for cross-region communication",
            allow_all_outbound=True
        )
        cross_region_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.all_icmp(), "Allow ICMP from anywhere")
        cross_region_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")

        key_names = {"us-east-1": "pams", "eu-west-1": "pans", "ap-southeast-1": "pam"}
        is_us_east = region == "us-east-1"
        
        instance = ec2.Instance(self, "TestInstance",
            vpc=self.vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC if is_us_east else ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_group=cross_region_sg,
            key_name=key_names.get(region)
        )

        CfnOutput(self, "VpcId", value=self.vpc.vpc_id, export_name=f"{self.stack_name}-VpcId")
        CfnOutput(self, "PrivateSubnetIds", value=",".join(self.private_subnet_ids), export_name=f"{self.stack_name}-PrivateSubnetIds")
        CfnOutput(self, "CrossRegionSecurityGroupId", value=cross_region_sg.security_group_id, export_name=f"{self.stack_name}-CrossRegionSGId")
        CfnOutput(self, "InstanceId", value=instance.instance_id, export_name=f"{self.stack_name}-InstanceId")
        CfnOutput(self, "InstancePrivateIp", value=instance.instance_private_ip, export_name=f"{self.stack_name}-PrivateIp")
from aws_cdk import Stack, CfnOutput, CustomResource, Duration, Aws
from aws_cdk import aws_ec2 as ec2, aws_lambda as lambda_, aws_iam as iam
from constructs import Construct

LAMBDA_CODE = """
import boto3
import json
import urllib3
import time

def handler(event, context):
    response_url = event['ResponseURL']
    
    def send_response(status, reason=None):
        response_body = {
            'Status': status,
            'Reason': reason or f'See CloudWatch Log Stream: {context.log_stream_name}',
            'PhysicalResourceId': event['LogicalResourceId'],
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId']
        }
        
        http = urllib3.PoolManager()
        try:
            http.request('PUT', response_url, body=json.dumps(response_body))
        except Exception as e:
            print(f"Failed to send response: {e}")
    
    try:
        if event['RequestType'] != 'Create':
            send_response('SUCCESS')
            return
        
        attachment_id = event['ResourceProperties']['AttachmentId']
        region = event['ResourceProperties']['Region']
        
        ec2 = boto3.client('ec2', region_name=region)
        
        for attempt in range(5):
            try:
                ec2.accept_transit_gateway_peering_attachment(TransitGatewayAttachmentId=attachment_id)
                send_response('SUCCESS', 'Peering attachment accepted successfully')
                return
            except Exception as e:
                print(f"Attempt {attempt + 1}: {e}")
                if attempt < 4:
                    time.sleep(30)
        
        send_response('FAILED', 'Failed to accept peering attachment after 5 attempts')
        
    except Exception as e:
        send_response('FAILED', str(e))
"""

class USEUPeeringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, us_tgw_id: str, eu_tgw_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, cross_region_references=True, **kwargs)

        peering = ec2.CfnTransitGatewayPeeringAttachment(self, "UStoEUPeering",
            transit_gateway_id=us_tgw_id,
            peer_transit_gateway_id=eu_tgw_id,
            peer_account_id=Aws.ACCOUNT_ID,
            peer_region="eu-west-1",
            tags=[{"key": "Name", "value": "US-to-EU-Peering"}]
        )

        acceptance_fn = lambda_.Function(self, "AcceptanceFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            timeout=Duration.minutes(5),
            code=lambda_.Code.from_inline(LAMBDA_CODE)
        )

        acceptance_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ec2:AcceptTransitGatewayPeeringAttachment", "ec2:DescribeTransitGatewayPeeringAttachments"],
            resources=["*"]
        ))

        CustomResource(self, "AcceptPeering",
            service_token=acceptance_fn.function_arn,
            properties={"AttachmentId": peering.ref, "Region": "eu-west-1"}
        )

        CfnOutput(self, "UStoEUPeeringId", value=peering.ref)

class USAPPeeringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, us_tgw_id: str, ap_tgw_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, cross_region_references=True, **kwargs)

        peering = ec2.CfnTransitGatewayPeeringAttachment(self, "UStoAPPeering",
            transit_gateway_id=us_tgw_id,
            peer_transit_gateway_id=ap_tgw_id,
            peer_account_id=Aws.ACCOUNT_ID,
            peer_region="ap-southeast-1",
            tags=[{"key": "Name", "value": "US-to-AP-Peering"}]
        )

        acceptance_fn = lambda_.Function(self, "AcceptanceFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            timeout=Duration.minutes(5),
            code=lambda_.Code.from_inline(LAMBDA_CODE)
        )

        acceptance_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ec2:AcceptTransitGatewayPeeringAttachment", "ec2:DescribeTransitGatewayPeeringAttachments"],
            resources=["*"]
        ))

        CustomResource(self, "AcceptPeering",
            service_token=acceptance_fn.function_arn,
            properties={"AttachmentId": peering.ref, "Region": "ap-southeast-1"}
        )

        CfnOutput(self, "UStoAPPeeringId", value=peering.ref)

class EUAPPeeringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, eu_tgw_id: str, ap_tgw_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, cross_region_references=True, **kwargs)

        peering = ec2.CfnTransitGatewayPeeringAttachment(self, "EUtoAPPeering",
            transit_gateway_id=eu_tgw_id,
            peer_transit_gateway_id=ap_tgw_id,
            peer_account_id=Aws.ACCOUNT_ID,
            peer_region="ap-southeast-1",
            tags=[{"key": "Name", "value": "EU-to-AP-Peering"}]
        )

        acceptance_fn = lambda_.Function(self, "AcceptanceFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            timeout=Duration.minutes(5),
            code=lambda_.Code.from_inline(LAMBDA_CODE)
        )

        acceptance_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ec2:AcceptTransitGatewayPeeringAttachment", "ec2:DescribeTransitGatewayPeeringAttachments"],
            resources=["*"]
        ))

        CustomResource(self, "AcceptPeering",
            service_token=acceptance_fn.function_arn,
            properties={"AttachmentId": peering.ref, "Region": "ap-southeast-1"}
        )

        CfnOutput(self, "EUtoAPPeeringId", value=peering.ref)
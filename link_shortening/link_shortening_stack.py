import json
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    aws_cloudfront as cf,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_lambda as lamb,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_route53 as route53,
)
from constructs import Construct

THIS_DIR = Path(__file__).parent.absolute()


class LinkShorteningStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        domain_name_param = cdk.CfnParameter(self, "DomainName")
        subdomain_param = cdk.CfnParameter(self, "Subdomain")
        hosted_zone_param = cdk.CfnParameter(self, "HostedZoneId")
        certificate_arn_param = cdk.CfnParameter(self, "CertificateArn")

        bucket = s3.Bucket(
            self,
            "Bucket",
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        fun = lamb.Function(
            self,
            "Function",
            code=self.link_function_code(bucket),
            handler="index.handler",
            runtime=lamb.Runtime.PYTHON_3_9,
        )
        fun.role.attach_inline_policy(
            self.allow_read_from_bucket(bucket, "GetLinksFromS3Policy")
        )

        cert = (
            certificate_arn_param.value_as_string
            and acm.Certificate.from_certificate_arn(
                self, "Certificate", certificate_arn_param.value_as_string
            )
        )
        dist = cf.Distribution(
            self,
            "Dist",
            domain_names=[
                f"{subdomain_param.value_as_string}.{domain_name_param.value_as_string}"
            ],
            certificate=cert,
            http_version=cf.HttpVersion.HTTP2_AND_3,
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3Origin(bucket),
                compress=False,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED_FOR_UNCOMPRESSED_OBJECTS,
                edge_lambdas=[
                    cf.EdgeLambda(
                        event_type=cf.LambdaEdgeEventType.ORIGIN_RESPONSE,
                        function_version=fun.current_version,
                    ),
                ],
            ),
        )

        zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "Zone",
            hosted_zone_id=hosted_zone_param.value_as_string,
            zone_name=domain_name_param.value_as_string,
        )
        route53.CnameRecord(
            self,
            "CNameRecord",
            zone=zone,
            delete_existing=True,
            record_name=subdomain_param.value_as_string,
            domain_name=dist.distribution_domain_name,
        )

        cdk.CfnOutput(self, "BucketName", value=bucket.bucket_name)

    def link_function_code(self, bucket: s3.Bucket):
        """
        Lambda@Edge does not support environment variables, so we hack them
        into the source code ourselves.
        """

        original_code = (THIS_DIR / "link_function.py").read_text()
        replaced = original_code.replace(
            'getenv("BUCKET_NAME")', json.dumps(bucket.bucket_name)
        )
        return lamb.InlineCode(replaced)

    def allow_read_from_bucket(self, bucket: s3.Bucket, policy_name: str):
        return iam.Policy(
            self,
            policy_name,
            document=iam.PolicyDocument(
                assign_sids=False,
                statements=[
                    iam.PolicyStatement(
                        actions=["s3:ListBucket"], resources=[bucket.bucket_arn]
                    ),
                    iam.PolicyStatement(
                        actions=["s3:GetObject"],
                        resources=[f"{bucket.bucket_arn}/*"],
                    ),
                ],
            ),
        )

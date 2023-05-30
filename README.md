# Serverless Link Shortener

To deploy, call `cdk deploy` with the required parameters:

```bash
cdk deploy --parameters DomainName=mydomain.tld \
           --parameters Subdomain=myurls \
           --parameters CertificateArn=arn:aws:acm:us-east-1:$AWS_ACCOUNT:certificate/... \
           --parameters HostedZoneId=ZZZZZZZZZZZZZ
```

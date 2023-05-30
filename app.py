#!/usr/bin/env python3
from os import getenv

import aws_cdk as cdk

from link_shortening.link_shortening_stack import LinkShorteningStack

app = cdk.App()
LinkShorteningStack(
    app,
    "LinkShorteningStack",
    env=cdk.Environment(
        account=getenv("CDK_DEFAULT_ACCOUNT"),
        region=getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()

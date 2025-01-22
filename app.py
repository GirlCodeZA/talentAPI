#!/usr/bin/env python3
import os
import sys

from aws_cdk import App
from talent_api.talent_api_stack import TalentApiStack

app = App()
TalentApiStack(app, "TalentApiStack")

app.synth()

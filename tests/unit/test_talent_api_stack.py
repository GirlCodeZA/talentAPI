import aws_cdk as core
import aws_cdk.assertions as assertions

from talent_api.talent_api_stack import TalentApiStack

# example tests. To run these tests, uncomment this file along with the example
# resource in talent_api/talent_api_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TalentApiStack(app, "talent-api")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class TalentApiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create DynamoDB table
        table = dynamodb.Table(
            self, "UserTable",
            partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            table_name="UserTable"  # Explicitly set table name
        )

        # Create Lambda function
        registration_function = _lambda.Function(
            self, "RegistrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="registration.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USERS_TABLE_NAME": table.table_name,
            }
        )

        # Grant Lambda permissions to DynamoDB
        table.grant_read_write_data(registration_function)

        # Create API Gateway
        api = apigateway.RestApi(self, "RegistrationApi",
            rest_api_name="Registration Service"
        )

        registration = api.root.add_resource("register")
        registration.add_method("POST", apigateway.LambdaIntegration(registration_function))
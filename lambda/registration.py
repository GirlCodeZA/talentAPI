import json
import boto3
from boto3.dynamodb.conditions import Key
from bcrypt import hashpw, gensalt

dynamo = boto3.resource('dynamodb')
table_name = os.environ['USERS_TABLE_NAME']
table = dynamo.Table(table_name)

def handler(event, context):
    try:
        body = json.loads(event['body'])
        name = body.get('name')
        surname = body.get('surname')
        email = body.get('email')
        password = body.get('password')

        # Check if the user already exists
        response = table.get_item(
            Key={'email': email}
        )
        if 'Item' in response:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'User already exists'})
            }

        # Hash the password
        hashed_password = hashpw(password.encode(), gensalt()).decode()

        # Save the user
        table.put_item(
            Item={
                'email': email,
                'name': name,
                'surname': surname,
                'password': hashed_password
            }
        )

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'User registered successfully'})
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal Server Error'})
        }

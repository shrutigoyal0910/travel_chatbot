import boto3
import json
from decouple import config

try:
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY')
    )
    print("Bedrock client initialized successfully")
    response = bedrock.invoke_model(
        modelId='meta.llama3-70b-instruct-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({"prompt": "Test message"})
    )
    result = response['body'].read().decode('utf-8')
    print(f"Bedrock response: {result}")
except Exception as e:
    print(f"Error: {str(e)}")
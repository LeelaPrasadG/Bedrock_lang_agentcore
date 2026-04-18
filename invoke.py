import boto3
import json
import uuid

def create_runtime_session_id() -> str:
    """Generate a unique session ID (33+ chars required by Bedrock AgentCore).
    Each unique session ID creates a new MicroVM."""
    return f"session-{uuid.uuid4()}"  # e.g. session-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (44 chars)

client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({"prompt": "What is famous in the Country that I Referred?"})

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:148018683714:runtime/agent_runtime_memory-WC2MrE3wP3',
    runtimeSessionId=create_runtime_session_id(),
    payload=payload,
    qualifier="DEFAULT" # This is Optional. When the field is not provided, Runtime will use DEFAULT endpoint
)
response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)
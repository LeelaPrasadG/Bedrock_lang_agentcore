# Bedrock AgentCore - LangGraph Agent

A LangGraph-based AI agent deployed on AWS Bedrock AgentCore Runtime.

---

## Steps

### 1. Setup Project Files

Copy the following 3 files into your project directory:
- `lauki_qna.csv`
- `pyproject.toml`
- `.sample_env` → rename to `.env`

---

### 2. Initialize Python Environment

```bash
uv init
uv sync
```

`uv sync` creates a Python virtual environment based on the dependencies defined in `pyproject.toml`.

---

### 3. Copy Agent Code

Copy `00_langgraph_agent.py` into the project directory.

---

### 4. Activate Virtual Environment

Switch to the newly created Python virtual environment:

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

---

### 5. Run the Agent Locally

Execute the agent using the Python executable from the `.venv`:

```powershell
D:\AI\Git\Bedrock_agentcore\.venv\Scripts\python.exe D:\AI\Git\Bedrock_agentcore\00_langgraph_agent.py
```

---

### 6. Modify Base Code for AWS Bedrock

The next step is to modify this base code to run in AWS Bedrock AgentCore Runtime. See steps below.

---

### 7. Create AWS Account

If you haven't done so already, create an AWS Account at [https://aws.amazon.com](https://aws.amazon.com).

---

### 8. Install AWS CLI

Install the AWS CLI to access AWS resources via the command line:
- Download from: [https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

---

### 9. Create IAM User & Group

1. Log in to the **AWS Console UI**
2. Navigate to **IAM → Users → Create User**
   - Username: `agentcore-Leela`
3. **Create Group**: `agentcore-ai`
4. Attach the following **Policy Permissions** to the group:
   - `AdministratorAccess`
   - `AmazonBedrockFullAccess`
   - `AWSCodeBuildAdminAccess`
   - `BedrockAgentCoreFullAccess`
5. Select the newly created group and complete user creation.

> **Note:** A User Group is a way to manage permissions for a team (e.g., Data Analysis, Data Engineering, AI Teams). Users are created as part of a group and inherit the group's policies.

---

### 10. Create Access Key

In the AWS Console, navigate to the newly created user and generate an **Access Key**. Download the CSV file containing the Access Key ID and Secret Access Key.

---

### 11. Configure AWS CLI

Configure the AWS CLI with the access key and secret:

```bash
aws configure
```

Verify the configuration by running:

```bash
aws sts get-caller-identity --no-cli-pager
```

---

### 12. Wrap Agent for Bedrock AgentCore Runtime

Make a copy of `00_langgraph_agent.py` and rename it to `01_agentcore_runtime.py`.

#### Add Imports

```python
# Import AgentCore runtime
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Create the AgentCore app instance
app = BedrockAgentCoreApp()
```

#### Add the Entrypoint Function

```python
# AgentCore Entrypoint
@app.entrypoint         # This decorator registers this function as the invocation handler
def agent_invocation(payload, context):
    """Handler for agent invocation in AgentCore runtime"""
    print("Received payload:", payload)
    print("Context:", context)

    # Extract query from payload
    query = payload.get("prompt", "No prompt found in input")

    # Invoke the graph
    result = agent.invoke({"messages": [("human", query)]})

    print("Result:", result)

    # Return the answer
    return {"result": result['messages'][-1].content}
```

#### Update `main`

```python
if __name__ == "__main__":
    app.run()
```

#### Invocation Sequence

```
app.run()
    └─> Starts HTTP server (local or on AWS Bedrock AgentCore Runtime)
            └─> AWS Bedrock sends HTTP POST with JSON payload + context
                    └─> @app.entrypoint routes request to agent_invocation()
                            └─> LangGraph agent processes the query and returns result
```

| Phase | Description |
|-------|-------------|
| **Startup** | `app.run()` starts an HTTP server that listens for incoming invocation requests from the Bedrock control plane — whether running locally or deployed as a container. |
| **Request** | AWS Bedrock AgentCore Runtime sends an HTTP POST to your container with a JSON payload (the user's input) and a context object (metadata: agent ID, session ID, etc.). |
| **Dispatch** | The `@app.entrypoint` decorator registers `agent_invocation` as the handler for incoming requests. |

---

### 13. Deploy to AWS Bedrock AgentCore Runtime

#### Check Available Commands

```bash
agentcore --help
```

#### Configure the Agent

The following command generates the `.bedrock_agentcore.yaml` configuration file:

```bash
agentcore configure -e ./01_agentcore_runtime.py
```

#### Launch the Agent

The following command deploys and launches the application in AWS Bedrock as a Runtime agent. The agent starts an HTTP server that listens for incoming invocation requests from the Bedrock control plane:

```bash
agentcore launch --env GROQ_API_KEY=gsk --env OPENAI_API_KEY=sk-proj
```

> **Deployment Type:** This deployment uses **direct code deploy** — the source code is packaged and deployed directly to AWS Bedrock AgentCore Runtime without building a custom Docker image.

---

## Deployment Options

| Method | Status | Description |
|--------|--------|-------------|
| Direct Code Deploy | ✅ Done | Source code is packaged and deployed directly. Used in the steps above. |
| Docker Container Deploy | ✅ Done | Deploy using a custom Docker image for full environment control. See steps below. |

---

## Docker Container Deployment

### 14. Reconfigure Agent for Docker Container Deploy

Run the configure command with the `--deployment-type container` flag and specify the target platform. This regenerates the `.bedrock_agentcore.yaml` and auto-generates a `Dockerfile` under `.bedrock_agentcore/<agent-name>/`:

```bash
agentcore configure -e ./01_agentcore_runtime.py --deployment-type container
```

The generated `.bedrock_agentcore.yaml` will look like:

```yaml
default_agent: agentcore_lang_docker_runtime
agents:
  agentcore_lang_docker_runtime:
    name: agentcore_lang_docker_runtime
    language: python
    entrypoint: ./01_agentcore_runtime.py
    deployment_type: container
    platform: linux/arm64
```

> **Note:** The `platform` defaults to `linux/arm64`. Change to `linux/amd64` if your target environment requires it.

---

### 15. Review the Auto-Generated Dockerfile

The toolkit generates a `Dockerfile` at `.bedrock_agentcore/agentcore_lang_docker_runtime/Dockerfile`. Key details:

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1

COPY . .
RUN cd . && uv pip install .
RUN uv pip install aws-opentelemetry-distro==0.12.2

# Run as non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

CMD ["opentelemetry-instrument", "python", "-m", "01_agentcore_runtime"]
```

> **Security note:** The container runs as a non-root user (`bedrock_agentcore`, UID 1000) for least-privilege execution.

---

### 16. Build & Push Docker Image to Amazon ECR

The `agentcore launch` command builds the Docker image, pushes it to Amazon Elastic Container Registry (ECR), and deploys it to AWS Bedrock AgentCore Runtime in a single step:

```bash
agentcore launch --env GROQ_API_KEY=gsk_... --env OPENAI_API_KEY=sk-proj-...
```

#### What happens under the hood

```
agentcore launch
    └─> Reads .bedrock_agentcore.yaml (deployment_type: container)
            └─> Builds Docker image from .bedrock_agentcore/agentcore_lang_docker_runtime/Dockerfile
                    └─> Creates/reuses an ECR repository and pushes the image
                            └─> Deploys the container to AWS Bedrock AgentCore Runtime
                                    └─> Agent is live and ready to receive invocations
```

| Phase | Description |
|-------|-------------|
| **Build** | Docker image is built locally using the auto-generated `Dockerfile`. |
| **Push** | Image is tagged and pushed to an Amazon ECR private repository in your AWS account. |
| **Deploy** | AWS Bedrock AgentCore Runtime pulls the image from ECR and starts the container. |
| **Runtime** | The container starts an HTTP server; AWS Bedrock routes invocation requests to `@app.entrypoint`. |

---

### 17. Invoke the Deployed Docker Agent

```bash
agentcore invoke "{'prompt': 'Tell me about Roaming Activations'}"
```

---

### Docker vs Direct Code Deploy — Comparison

| Aspect | Direct Code Deploy | Docker Container Deploy |
|--------|--------------------|------------------------|
| Build step | None | Docker image build + ECR push |
| Environment control | Managed by Bedrock | Full control via `Dockerfile` |
| Custom system dependencies | Not supported | Supported (add to `Dockerfile`) |
| Reproducibility | Runtime-managed | Image-pinned |
| Cold start | Faster | Slightly slower (image pull) |
| Recommended for | Quick prototyping | Production workloads |

---

## AgentCore Memory

### 18. Create Memory in AWS Console

1. Go to **AWS Console** → search **Bedrock AgentCore**
2. Navigate to **Memory** → **Create Memory**
3. Set a name (e.g., `customercare_agent_memory`)
4. AWS creates a `MEMORY_ID` in the format `<name>-<random-suffix>` (e.g., `customercare_agent_memory-VNlpNwG2Y0`)
5. Note the **Memory ID** — it is required in `02_agentcore_memory.py`

> Memory persists conversation history and user preferences across sessions using `AgentCoreMemorySaver` (short-term checkpointing) and `AgentCoreMemoryStore` (long-term semantic store).

---

### 19. Create `02_agentcore_memory.py`

Copy `01_agentcore_runtime.py` → rename to `02_agentcore_memory.py`, then add:

#### Key imports

```python
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore
from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
```

#### Memory configuration

```python
MEMORY_ID = "customercare_agent_memory-VNlpNwG2Y0"  # From AWS Console

checkpointer = AgentCoreMemorySaver(memory_id=MEMORY_ID)  # Short-term: tracks thread history
store = AgentCoreMemoryStore(memory_id=MEMORY_ID)         # Long-term: semantic user memory
```

#### MemoryMiddleware hooks

```python
class MemoryMiddleware(AgentMiddleware):
    def pre_model_hook(self, state, config, *, store):
        # Saves latest human message; retrieves past preferences before LLM call
        ...
    def post_model_hook(self, state, config, *, store):
        # Saves AI response to long-term memory after LLM call
        ...
```

#### Create agent with memory

```python
agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=checkpointer,   # Short-term memory (per thread)
    store=store,                 # Long-term memory (across threads)
    middleware=[MemoryMiddleware()],
    system_prompt=system_prompt,
)
```

#### Entrypoint — pass `actor_id` and `thread_id`

```python
@app.entrypoint
def agent_invocation(payload, context):
    actor_id  = payload.get("actor_id", "default-user")
    thread_id = payload.get("thread_id", "default-session")
    config = {"configurable": {"thread_id": thread_id, "actor_id": actor_id}}
    result = agent.invoke({"messages": [("human", query)]}, config=config)
    return {"result": result['messages'][-1].content, "actor_id": actor_id, "thread_id": thread_id}
```

| Memory Component | Role |
|-----------------|------|
| `AgentCoreMemorySaver` | Short-term checkpointer — persists message history per `thread_id` |
| `AgentCoreMemoryStore` | Long-term store — semantic search across all sessions for an `actor_id` |
| `pre_model_hook` | Runs before LLM call — saves human message, retrieves relevant past memories |
| `post_model_hook` | Runs after LLM call — saves AI response to long-term store |

---

### 20. Deploy Memory Agent

#### Configure

```bash
agentcore configure -e ./02_agentcore_memory.py --deployment-type container
```

#### Launch

```bash
agentcore launch --env GROQ_API_KEY=gsk_... --env OPENAI_API_KEY=sk-proj-...
```

#### Test via CLI

```bash
agentcore invoke "{'prompt': 'What is famous in the Country that I Referred?'}"
```

---

### 21. Invoke Runtime Externally via `invoke.py`

Use `invoke.py` to call any deployed AgentCore runtime directly via the **boto3 SDK** — no CLI needed.

```python
import boto3, json, uuid

def create_runtime_session_id() -> str:
    """Each unique session ID creates a new MicroVM (must be 33+ chars)."""
    return f"session-{uuid.uuid4()}"   # 44 chars

client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({"prompt": "What is famous in the Country that I Referred?"})

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:<region>:<account-id>:runtime/<runtime-id>',
    runtimeSessionId=create_runtime_session_id(),
    payload=payload,
    qualifier="DEFAULT"  # Optional — omit to use the DEFAULT endpoint
)
response_data = json.loads(response['response'].read())
print("Agent Response:", response_data)
```

#### Key parameters

| Parameter | Where to find it | Notes |
|-----------|-----------------|-------|
| `agentRuntimeArn` | AWS Console → Bedrock AgentCore → Agent Runtimes → copy ARN | Required |
| `runtimeSessionId` | Generate locally — must be 33+ chars | Each new ID = new MicroVM |
| `qualifier` | AWS Console → Agent Runtime → Endpoints tab → copy Endpoint ARN | Optional; defaults to `DEFAULT` |
| `region_name` | Must match the region where the agent is deployed | Required |

#### Run

```bash
python invoke.py
```

---

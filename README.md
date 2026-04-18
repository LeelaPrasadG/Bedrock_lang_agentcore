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

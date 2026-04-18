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
| Docker Container Deploy | 🔜 Coming Soon | Deploy using a custom Docker image for full environment control. *(Details to be added)* |

---

# Designing an Autonomous E-commerce Support Crew

A step-by-step guide to building the **Course-end Project — AI Agents: Multi-agent Design and Governance** on a local Flowise instance.

This guide walks you through designing and building a multi-agent "crew" of specialized AI support agents for **Future Gadgets Inc.**, an e-commerce store whose human support team is overwhelmed by repetitive queries. You will act as an **AI Systems Architect** and build a prototype in **Flowise** that understands user intent and routes each query to the right specialist agent.

---

## Overview

- **Scenario**: Future Gadgets Inc. receives a high volume of repetitive support queries in three categories: product information, order status, and promotions & deals.
- **Your mission**: Design and build a multi-agent prototype that autonomously handles these queries and routes them to the correct specialist.
- **Tools**: Flowise AI (this local instance) and a text editor for documentation.
- **Learning objectives**:
  1. Design a multi-agent system architecture with at least three specialized agent roles and a central orchestrator.
  2. Implement a coordinated workflow in Flowise that routes user queries to the appropriate agent.
  3. Develop a basic governance plan that identifies risks and proposes mitigations.
  4. Analyze the trade-offs between agent autonomy and system-level control.

### Grading deliverables

| # | Deliverable | Format |
|---|-------------|--------|
| 1 | Full-screen screenshot of the final Orchestrator canvas showing the routing node and connections to >=3 specialists | PNG / JPG / JPEG |
| 2 | Design methodology explanation (150-200 words) | PDF / DOCX / TXT |
| 3 | Risk & governance analysis (200-300 words, >=2 risks each with one mitigation) | PDF / DOCX / TXT |
| 4 | Reflection & learning insights (250 words) | PDF / DOCX / TXT |

---

## Prerequisites

Before you start, confirm the following:

- **Flowise is running and healthy** - the local instance runs as a Docker container `docker-flowise-1` (image `flowiseai/flowise:3.1.3`). Verify with:

  ```bash
  docker ps --filter "name=flowise"
  ```

  You should see `docker-flowise-1 ... Up ... (healthy)`.

- **Access the Flowise UI** at `http://localhost:3000`.

- **An LLM provider credential** - create or select one inside the Flowise UI (left panel, **Credentials**). Flowise is provider-agnostic: you configure a chat model node (e.g., `ChatOpenAI`, `Deepseek`, `Groq`) with credentials from your chosen provider. Never paste API keys into committed notes; create them per-node in the UI.

- **Optional**: a product FAQ text file if you want to give the Product Agent a knowledge source (see the Advanced path below).

---

## Architecture

The system uses a **one orchestrator, three specialist** design:

```text
                   ORCHESTRATOR AGENT
              (Multi Prompt Router - the brain)
                routes: product_info
                        order_status
                        promotions
                        |      |      |
              +---------+      |      +---------+
              |                |                |
        PRODUCT INFO     ORDER STATUS    PROMOTIONS
          Agent             Agent            Agent
```

**Architecture roles**:

- **Orchestrator Agent**: the user's single point of contact. It analyzes the query and routes it to the correct specialist.
- **Product Info Agent**: answers questions about product features, specifications, and availability.
- **Order Status Agent**: responds to questions about order location and estimated delivery date.
- **Promotions Agent**: informs users about current sales, discounts, and special offers.

---

## Part 1: System Design & Specialist Agents

This part builds the three specialist chatflows, each saved under a clear name. In Flowise, a **chatflow** is a canvas of connected nodes.

### Node vocabulary

Use these Flowise nodes. Categories are in parentheses; all are verified present in the local Flowise source checkout:

| Guide term | Flowise category | Purpose |
|-----------|------------------|---------|
| LLM Chain | Chains | Produces a response from a chat model given a prompt |
| Chat Model (e.g. ChatOpenAI / Deepseek / Groq) | Chat Models | The model provider behind each agent |
| Multi Prompt Chain | Chains | The orchestrator's routing "brain" |
| Prompt Retriever | Retrievers | Defines a route's name, description, and prompt |
| Chatflow Tool | Tools | Invokes another chatflow (links a route to a specialist) |
| Chatflow API credential | Credentials | Auth used by each Chatflow Tool |

> **Compatibility note**: The assignment PDF (and older Flowise versions) refers to the connection node as the **"Chatflow"** node. In Flowise 3.x this node is named **Chatflow Tool** in the **Tools** category. The behavior - one chatflow invoking another - is the same.

### Create the Product Info Agent

1. Click **+ Add New** and select **Chatflow**.
2. From **Chains**, drag an **LLM Chain** onto the canvas.
3. From **Chat Models**, add a **Chat Model** node (e.g., `ChatOpenAI` or your provider) and configure its credential and model name.
4. Connect the Chat Model to the LLM Chain.
5. Set a **Prompt** for the LLM Chain giving it a **product expert persona**:

   ```text
   You are a friendly product expert at Future Gadgets Inc. Answer general questions
   about our products, their features, specifications, and availability. Be helpful,
   concise, and admit when you do not know the answer.
   ```

6. **Save** the chatflow and name it **"Product Agent"**.

> **Advanced path**: For more grounded answers, add a **Document Loader** (e.g., a **Text File** loader with your product FAQ file) so the agent answers from the FAQ content.

### Create the Order Status Agent

1. Create a new **Chatflow**.
2. Add an **LLM Chain** and a **Chat Model** with credentials as above.
3. Set a prompt that defines its single job - order status - and that it should **ask the user for an order number** first, then provide a **simulated static response**:

   ```text
   You are the Order Status Agent at Future Gadgets Inc. Your only job is to help with
   questions about order status. First ask the customer for their order number, then
   provide a simulated response such as: "Orders are typically delivered within
   3-5 business days."
   ```

4. Save the chatflow as **"Order Agent"**.

### Create the Promotions Agent

1. Create a new **Chatflow**.
2. Add an **LLM Chain** and a **Chat Model**.
3. Configure a prompt that acts as a **sales assistant** and mentions a **fictional sale**:

   ```text
   You are a sales assistant at Future Gadgets Inc. Inform customers about our latest
   deals and promotions. We are currently offering a 20% discount on all smartwatches!
   ```

4. Save as **"Promotions Agent"**.

### Quick test - specialist agents

Open each chatflow's **chat canvas** and send a matching probe to confirm on-topic responses:

- Product Agent: "Does the X2000 drone have a 4K camera?"
- Order Agent: "Where is my order #58291?" - expect it to ask for/acknowledge the order number and give a static delivery estimate.
- Promotions Agent: "Are there any offers right now?" - expect the fictional sale info.

---

## Part 2: Building the Central Orchestrator

The orchestrator is the user's **single point of contact** and the heart of the system.

### 1. Create the orchestrator

Create a new primary chatflow (e.g., **"Orchestrator Agent"**). This is the chatflow whose canvas you will capture for Deliverable 1.

### 2. Add the router node (the "brain")

1. From **Chains**, add the **Multi Prompt Chain** node.
2. Connect your **Chat Model** to it (same provider node).

> **Note**: In Flowise 3.x the Multi Prompt Chain used by the assignment is marked **DEPRECATING** in the UI, but it remains the documented, assignment-intended node for this prototype.

### 3. Define the routing logic

The Multi Prompt Chain reads a set of **routes**, each defined by a **Prompt Retriever** node (from **Retrievers**). Add three **Prompt Retriever** nodes and fill in the fields:

| Prompt Name | Prompt Description | Prompt System Message |
|------------|--------------------|----------------------|
| `product_info` | Routes questions about product features, details, or specifications. | You are the Product Expert at Future Gadgets Inc. Answer about products. |
| `order_status` | Routes questions about order tracking, shipping, or delivery dates. | You are the Order Agent at Future Gadgets Inc. Ask for the order number and give a simulated delivery estimate (3-5 business days). |
| `promotions` | Routes questions about current sales, discounts, and special offers. | You are the Sales Assistant at Future Gadgets Inc. We are currently offering a 20% discount on all smartwatches. |

The **Prompt Name** and **Prompt Description** are what the router uses to decide which route fits the user's query, so keep them descriptive and mutually exclusive.

### 4. Create the Chatflow API credential

Each connection from the orchestrator to a specialist chatflow uses a `Chatflow Tool`, which requires a **Chatflow API** credential:

1. In the left panel go to **Credentials** and **Add a credential**.
2. Choose **Chatflow API** and generate a key.
3. Save it and note the key for the next step.

### 5. Connect the specialist agents

1. From **Tools**, add a **Chatflow Tool** node for each specialist:
   - "Product Agent"
   - "Order Status Agent"
   - "Promotions Agent"
2. For each **Chatflow Tool**:
   - **Select Chatflow**: choose the specialist chatflow from the list.
   - **Connect Credential**: the **Chatflow API** credential you created.
3. Wire each **Chatflow Tool** into the orchestrator so the router can call it. The final canvas should look like the architecture diagram above - the **Multi Prompt Chain** in the center connected to the three specialist chatflows.

### Test your system

Open the orchestrator chatflow's **chat canvas** and send the three probes, verifying each is routed to the correct specialist:

- Product: "Does the X2000 drone have a 4K camera?" -> Product Agent
- Order: "Where is my order #58291?" -> Order Agent
- Promotions: "Is there a discount on smartwatches?" -> Promotions Agent

---

## Part 3: Governance & Documentation

Compile the four deliverables into a single report (save as PDF) for submission and peer review.

### Deliverable 1 - Final System Architecture

Upload a single **full-screen screenshot** (PNG, JPG, or JPEG) of the final **Orchestrator Agent** canvas. It must clearly show the central routing node (`Multi Prompt Chain`) and its connections to the at least three specialist chatflows.

### Deliverable 2 - Design Methodology (150-200 words)

Explain your design methodology. Describe the purpose of each of the three specialists and justify the routing descriptions you created for the orchestrator - how they help the router make accurate decisions.

### Deliverable 3 - Risk & Governance Analysis (200-300 words)

Identify at least **two distinct risks** (e.g., an agent providing incorrect information, handling sensitive user data, agent hallucinations) and propose **one specific mitigation** for each.

| Risk | Mitigation |
|------|-----------|
| Agent gives incorrect product/order info | Scope each agent to its domain prompt and validate responses against the FAQ source |
| Agent hallucinates or overstates promotions | Simulate static, vetted data in prompts; monitor and log conversations |

### Deliverable 4 - Reflection & Learning Insights (250 words)

Describe how you approached the AI agents design and the key insights you will apply in future projects.

### Report compilation & sharing

1. Compile the architecture screenshot and the three written sections into a single document.
2. Save the report as **PDF**.
3. Upload to the **Peer Review** area of the course shell with a brief description.
4. Optionally review peers' submissions and provide constructive feedback.

---

## Troubleshooting

- **Empty or generic responses**: check the chat model node has a valid credential and model name; confirm the prompt is set on the right node.
- **Query routed to the wrong agent**: tighten the **Prompt Description** for each route so intents do not overlap.
- **Cannot find a node**: node category or name differs between Flowise versions - the assignment's "Chatflow" node is the **Chatflow Tool** in Flowise 3.x, and also confirms your Flowise version by checking the left node panel.

---

## References

- Assignment: "Course-end Project - AI agents - multi-agent design and governance" (Coursera).
- Flowise source and configuration: `C:\working\projects\ai-projects\Flowise` (docker-compose, README, `.env.example`).
- This instance: Docker container `docker-flowise-1` (image `flowiseai/flowise:3.1.3`) at `http://localhost:3000`.
# Scalable Chat Application on AWS
A real-time chat application built with Python/Flask and deployed on a scalable, high-availability AWS infrastructure. This project was created as a hands-on exercise to demonstrate cloud architecture and deployment skills.

## Core Features
* **User System:** Automatic user creation on login.
* **Chat Rooms:** Private, one-on-one conversations.
* **Persistent Data:** User and message history stored in DynamoDB.
* **Health Check:** A /health endpoint for load balancer integration.

## Cloud Architecture
The architecture was designed for high availability and scalability, distributing the application across multiple Availability Zones.

![Architecture Diagram](architecture-diagram.png)

*(Note: Replace with your architecture diagram image)*

**The request flow is as follows:**
* A custom domain in **Route 53** points to an **Application Load Balancer (ELB)**.
* The ELB terminates SSL using a certificate from **ACM** and distributes traffic to a **Target Group**.
* The Target Group routes requests to healthy **EC2 instances**, which are monitored via the /health endpoint.
* The application runs inside a **Docker** container on each EC2 instance and communicates with **DynamoDB** for data persistence.

## Running Locally

### 1. AWS Pre-requisites
Create two DynamoDB tables: alex-users (Primary Key: username) and alex-messages (Primary Key: message_id). The alex-messages table requires a Global Secondary Index named UserConversation with a partition key of conversation_id (String) and a sort key of timestamp (Number).

### 2. Configure Environment
Create a .env file in the project root:

```env
# .env file
FLASK_SECRET_KEY="A_RANDOM_SECRET_KEY_HERE"
AWS_REGION="your-aws-region"
DYNAMODB_USERS_TABLE="alex-users"
DYNAMODB_MESSAGES_TABLE="alex-messages"
```

### 3. Install & Run
Clone the repo and install dependencies:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

**To run with Docker (Recommended):**

```bash
# Build the image
docker build -t flask-chat-app .

# Run the container (ensure your AWS credentials are in your environment)
docker run -p 5000:5000 --env-file .env flask-chat-app
```

# Stage 2: AI Chatbot Service - Design Document

**Date:** 2026-03-11
**Status:** Implemented
**Author:** AI Learning Roadmap Project

---

## 1. Overview

This document outlines the architectural decisions and design rationale for Stage 2 of the AWS AI Terraform Learning Roadmap: a serverless AI chatbot service.

### 1.1 Goals

- Build a scalable serverless API for AI conversations
- Integrate AWS Bedrock Claude API
- Implement proper security with Secrets Manager
- Establish monitoring and observability
- Learn serverless patterns and tradeoffs

### 1.2 Success Criteria

- Working REST API endpoint
- Successful integration with Bedrock
- Proper error handling and logging
- Deployable with single `terraform apply` command
- Comprehensive monitoring

---

## 2. Architecture Decisions

### 2.1 Compute: Serverless (Lambda) vs Containers vs VMs

| Aspect | Serverless (Lambda) | Containers (ECS) | VMs (EC2) |
|--------|---------------------|------------------|-----------|
| **Cost** | Pay-per-use, free tier | Per-hour billing | Per-hour billing |
| **Scaling** | Automatic, instant | Manual/auto scaling | Manual scaling |
| **Operations** | Zero server management | Container management | Full server management |
| **Cold Starts** | Yes (100-500ms) | No | No |
| **Execution Limit** | 15 minutes | Unlimited | Unlimited |
| **Complexity** | Low | Medium | High |

#### Decision: Serverless (Lambda)

**Reasons:**

1. **Cost Efficiency**
   - Pay only for actual compute time
   - Generous free tier (1M requests/month)
   - No idle costs

2. **Development Speed**
   - Faster iteration cycles
   - No infrastructure to manage
   - Focus on business logic

3. **Automatic Scaling**
   - Handles traffic spikes automatically
   - No capacity planning needed
   - 1000 concurrent execution limit

4. **Learning Value**
   - Modern cloud-native pattern
   - Event-driven architecture
   - Microservices best practices

**Tradeoffs:**

✅ **Pros:**
- Lowest cost for sporadic traffic
- Auto-scaling built-in
- Zero operational overhead
- Integrated monitoring
- Fast deployment

❌ **Cons:**
- Cold start latency (~100-500ms)
- 15-minute execution limit
- 6MB payload limit
- Vendor lock-in
- Debugging complexity

**Mitigation Strategies:**
- Use provisioned concurrency if cold starts are critical (not needed for dev)
- Design for idempotency to handle retries
- Keep payload under 6MB
- Use CloudWatch for debugging

**Limitations & Considerations:**

- **Technical**: 15-minute timeout, 6MB payload, 256MB deployment package
- **Cost**: High-frequency requests may be more expensive than containers
- **Scalability**: Regional limit of 1000 concurrent executions
- **Security**: VPC configuration adds complexity

### 2.2 API Layer: API Gateway vs ALB vs Direct Lambda

| Aspect | API Gateway | ALB | Direct Lambda |
|--------|-------------|-----|---------------|
| **Features** | Throttling, auth, caching | L7 routing, health checks | Lambda URL only |
| **Cost** | Per-request + data | Per-hour + LCUs | Per-request |
| **Complexity** | Medium | Medium | Low |
| **AWS Integration** | Excellent | Good | Limited |

#### Decision: API Gateway

**Reasons:**
- Native Lambda integration
- Built-in authentication support (for Stage 6)
- Request/response transformation
- Usage plans and throttling
- AWS managed service

### 2.3 Secret Storage: Secrets Manager vs Parameter Store vs Environment Variables

| Aspect | Secrets Manager | Parameter Store | Env Variables |
|--------|----------------|-----------------|---------------|
| **Rotation** | Automatic | Manual | No |
| **Cost** | $0.40/month/secret | Free tier | Free |
| **Encryption** | Automatic | Automatic | No |
| **Audit** | CloudTrail | CloudTrail | No |

#### Decision: Secrets Manager

**Reasons:**
- Automatic secret rotation (for production)
- Fine-grained IAM policies
- Audit logging via CloudTrail
- Secure by default
- Low cost for learning project

---

## 3. System Design

### 3.1 Components

```
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                          │
│                  (REST API + CORS)                       │
└────────────────────┬────────────────────────────────────┘
                     │ POST /chat
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Lambda Function                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Handler (chat.py)                                │  │
│  │  - Request validation                            │  │
│  │  - Error handling                                │  │
│  │  - Response formatting                           │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LLM Service (llm_service.py)                     │  │
│  │  - Bedrock client                                 │  │
│  │  - Conversation management                        │  │
│  │  - Prompt engineering                             │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├──────────────┐
                     ▼              ▼
            ┌─────────────┐  ┌──────────────┐
            │  Bedrock    │  │   Secrets    │
            │   (Claude)  │  │   Manager    │
            └─────────────┘  └──────────────┘
                     │
                     ▼
            ┌────────────────────────────────┐
            │         CloudWatch             │
            │  - Logs (Lambda + API GW)      │
            │  - Metrics (invocations, etc)  │
            │  - Alarms (errors, latency)    │
            │  - Dashboard                   │
            └────────────────────────────────┘
```

### 3.2 Data Flow

1. **Request**: Client POSTs to API Gateway `/chat` endpoint
2. **Validation**: API Gateway passes to Lambda (proxy integration)
3. **Processing**: Lambda validates request body and message
4. **LLM Call**: Lambda calls Bedrock via SDK
5. **Response**: Bedrock returns generated text
6. **Logging**: All steps logged to CloudWatch
7. **Return**: Response formatted and returned to client

### 3.3 Security Model

**IAM Roles:**
- Lambda execution role with least privilege
- Separate policies for Bedrock and Secrets Manager
- No AWS credentials in code

**Secrets Manager:**
- API keys stored securely
- IAM policy restricts access
- Automatic encryption (KMS)

**Network:**
- Lambda runs outside VPC (accesses public AWS services directly)
- No VPC dependencies required
- All services (Bedrock, Secrets Manager, CloudWatch) accessed via public endpoints
- Stage 2 can deploy independently of Stage 1

---

## 4. Implementation Details

### 4.1 Lambda Function

**Runtime:** Python 3.11
**Handler:** `handlers/chat.handler`
**Timeout:** 30 seconds (configurable)
**Memory:** 256 MB (configurable)

**Dependencies:**
- `boto3`: AWS SDK
- `aws-lambda-powertools`: Logging and tracing
- `requests`: HTTP client (fallback)

**Error Handling:**
- Validation errors → 400
- Bedrock errors → 500 with logging
- Timeout errors → Lambda retry

### 4.2 API Gateway

**Type:** REST API (regional)
**Endpoints:**
- `POST /chat` - Main chat endpoint
- `OPTIONS /chat` - CORS preflight

**CORS Configuration:**
- Allow all origins (`*`) for development
- Restrict in production
- Headers: Content-Type, Authorization, X-Api-Key

**Integration:** AWS_PROXY (direct Lambda mapping)

### 4.3 Monitoring Strategy

**Metrics:**
- Lambda invocations, errors, duration, throttles
- API Gateway count, 4XX, 5XX, latency

**Logs:**
- Structured JSON logs
- Log level: INFO (configurable)
- Retention: 7 days

**Alarms:**
- Lambda errors > 5 in 5 minutes
- Lambda duration > 10s
- API Gateway 5XX > 10 in 5 minutes

**Dashboard:**
- Real-time metrics visualization
- Log query interface
- Single pane of glass

---

## 5. Cost Analysis

### 5.1 Monthly Cost Estimate (Dev Environment)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 100K requests, 256MB, 5s avg | $0.00 (free tier) |
| API Gateway | 100K requests, 1KB avg | $0.00 (free tier) |
| CloudWatch Logs | 5GB logs | $0.50 |
| CloudWatch Alarms | 3 metrics, 10 alarms | $0.30 |
| Secrets Manager | 1 secret | $0.40 |
| **Total** | | **~$1.20/month** |

### 5.2 Production Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 10M requests, 512MB, 5s avg | $30.00 |
| API Gateway | 10M requests, 1KB avg | $3.50 |
| CloudWatch Logs | 50GB logs | $5.00 |
| CloudWatch Alarms | 10 metrics, 30 alarms | $3.00 |
| Secrets Manager | 1 secret | $0.40 |
| **Total** | | **~$41.90/month** |

### 5.3 Cost Optimization Tips

1. **Lambda**: Optimize memory/performance ratio
2. **API Gateway**: Enable caching for repeated requests
3. **CloudWatch**: Reduce log retention for dev
4. **Data Transfer**: Minimize response sizes

---

## 6. Testing Strategy

### 6.1 Unit Tests

- Test LLM service with mock Bedrock responses
- Validate request/response parsing
- Test error handling paths

### 6.2 Integration Tests

- Deploy to test environment
- Test actual API endpoint
- Verify Bedrock integration
- Check CloudWatch logs

### 6.3 Load Tests

- Use tools like Locust or Artillery
- Test concurrent requests
- Measure cold start impact
- Validate auto-scaling

---

## 7. Deployment Strategy

### 7.1 Development

1. Local testing with AWS SAM CLI (optional)
2. Terraform apply to dev account
3. Manual testing via curl/Postman
4. Review CloudWatch logs

### 7.2 Production (Future)

1. CI/CD pipeline with GitHub Actions
2. Automated testing before deploy
3. Blue-green deployment via API Gateway stages
4. Automated rollback on failure
5. Canary deployment with weighted routing

---

## 8. Future Enhancements

### 8.1 Stage 3+ Integration

- Document upload via S3
- Conversation history in DynamoDB
- Context from RAG system (Stage 4)
- Tool use for Agent (Stage 5)

### 8.2 Features

- Streaming responses (SSE)
- Multi-turn conversation memory
- User authentication (Cognito)
- Rate limiting
- A/B testing for prompts

### 8.3 Infrastructure

- Multi-region deployment
- Custom domain name
- AWS WAF for security
- X-ray tracing
- Lambda@Edge for global

---

## 9. Lessons Learned

### 9.1 What Went Well

- Serverless architecture simplified deployment
- Terraform modules enabled reusability
- CloudWatch provided excellent visibility
- Bedrock integration was straightforward

### 9.2 Challenges

- Cold start latency (mitigated with optimal memory)
- Terraform state management (use backend)
- Local testing limitations (use SAM CLI)
- Debugging Lambda errors (use CloudWatch)

### 9.3 Recommendations

1. Start with serverless for learning
2. Invest in monitoring early
3. Use infrastructure as code
4. Test error handling thoroughly
5. Document architectural decisions

---

## 10. Conclusion

Stage 2 successfully demonstrates a production-ready serverless AI chatbot using AWS managed services. The architecture provides:

- **Simplicity**: Minimal operational overhead
- **Scalability**: Automatic scaling to 1000 concurrent
- **Security**: IAM roles, Secrets Manager, encryption
- **Observability**: Comprehensive monitoring and logging
- **Cost-effectiveness**: Pay-per-use pricing

This foundation will support more complex features in subsequent stages while maintaining the serverless-first approach.

---

**Design Approved:** 2026-03-11
**Next Stage:** Document Analysis System (Stage 3)

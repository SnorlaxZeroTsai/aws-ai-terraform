# Stage 1: Terraform Foundation - Architecture Design

## 1. Architecture Overview

```
                              Internet
                                 |
                                 v
                        [ Route Table - Public ]
                                 |
                    +------------+------------+
                    |            |            |
              [ AZ-1 ]        [ AZ-2 ]      [ Future AZ-3 ]
                    |            |            |
           +--------+--------+   |   +--------+--------+
           |                 |   |   |                 |
    [ Public Subnet ]  [ Public Subnet ]  [ Public Subnet ]
    10.0.1.0/24       10.0.2.0/24       10.0.3.0/24
           |                 |                 |
    [ Internet Gateway ]-----+-----------------+
           |
           +-------------------------------------+
                    |
           [ Private Subnets ]
           10.0.11.0/24 (AZ-1)
           10.0.12.0/24 (AZ-2)
                    |
           [ NAT Gateway ] (AZ-1)
                    |
           +--------+--------+
           |                 |
    [ Application ]    [ Database - Future ]
    EC2 Instances            |
                            v
                     [ EBS Volumes ]
```

**Network Layout:**
- **VPC CIDR:** 10.0.0.0/16 (65,536 available IPs)
- **Public Subnets:** 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
- **Private Subnets:** 10.0.11.0/24 (AZ-1), 10.0.12.0/24 (AZ-2)
- **Availability Zones:** 2 AZs for high availability
- **NAT Gateway:** Single gateway in AZ-1 for cost optimization

**Component Summary:**
- **VPC:** Isolated network environment
- **Internet Gateway:** Public internet access
- **NAT Gateway:** Private subnet outbound internet access
- **Route Tables:** Public (IGW) and Private (NAT) routing
- **Security Groups:** Tiered access control (Web, App, DB)
- **IAM Roles:** Instance profiles for EC2 permissions
- **EC2 Instances:** t3.micro in private subnets

---

## 2. Design Decisions

### Decision 1: Multi-AZ Architecture

**Problem Statement:**
How many Availability Zones should we deploy across to balance high availability, cost, and complexity for our initial infrastructure?

**Options Considered:**
- **Option A:** Single AZ deployment
- **Option B:** 2 AZ deployment
- **Option C:** 3+ AZ deployment

**Selection:**
**Option B: 2 AZ deployment**

**Reasoning:**
Two AZs provide significant availability improvements over a single AZ while keeping costs manageable. This is the sweet spot for initial deployment - we gain protection against AZ failures without the 50% cost increase of going to 3 AZs.

**Pros:**
✅ High availability - survives single AZ failures
✅ **✅ Reasonable cost - only ~2x infrastructure costs**
✅ **✅ Proven architecture pattern - AWS recommends 2 AZs as minimum for production**
✅ **✅ Manageable complexity - easier to understand and troubleshoot**
✅ **✅ Good foundation - can add third AZ later if needed**
✅ Supports blue-green deployments across AZs

**Cons:**
❌ Still vulnerable to regional failures (affects all AZs)
❌ **❌ ~2x cost compared to single AZ**
❌ **❌ Increased complexity in networking and routing**
❌ **❌ Cross-AZ data transfer costs ($0.01/GB)**
❌ Potential for asymmetric routing issues

**Mitigation Strategies:**
- Use Auto Scaling Groups to distribute instances evenly
- Implement cross-AZ monitoring and alerting
- Design stateless applications that can failover between AZs
- Use EBS snapshots for backup across AZs
- Test AZ failure scenarios during development

**Constraints:**
- 📊 **Technical:** Must use same instance types across AZs for consistency
- 💰 **Cost:** ~2x infrastructure costs, cross-AZ data transfer at $0.01/GB
- 📈 **Scalability:** Can add third AZ later without major redesign
- 🔒 **Security:** Security groups and NACLs must span all AZs

**Why Not Other Options:**
- **Option A (Single AZ):** No high availability - single point of failure. If the AZ has issues, entire application goes down. Not suitable for production workloads.
- **Option C (3+ AZs):** Overkill for initial deployment. 3 AZs cost 3x and add complexity without proportional benefit for starting out. Can upgrade later if needed.

---

### Decision 2: Public vs Private Subnets

**Problem Statement:**
Should we deploy our application servers in public subnets (directly accessible from internet) or private subnets (accessed through load balancer/NAT)?

**Options Considered:**
- **Option A:** All resources in public subnets
- **Option B:** Hybrid approach - public subnets for bastion/ALB, private for applications
- **Option C:** All resources in private subnets with VPN/Direct Connect

**Selection:**
**Option B: Hybrid approach**

**Reasoning:**
The hybrid approach follows AWS best practices - public subnets for internet-facing resources (ALB, bastion), private subnets for application servers. This provides a layered defense where application servers have no direct public IP addresses, reducing attack surface while maintaining necessary connectivity.

**Pros:**
✅ **✅ Defense in depth - application servers not directly accessible**
✅ **✅ Flexible architecture - can place resources where appropriate**
✅ **✅ Bastion host for secure SSH access**
✅ **✅ Cost-effective - NAT only for private subnets that need it**
✅ **✅ Scales well - can add more private subnets as needed**
✅ **✅ AWS best practice - recommended architecture pattern**

**Cons:**
❌ **❌ NAT Gateway costs - ~$32/month plus data processing**
❌ **❌ Increased complexity - more routing tables and rules**
❌ **❌ Troubleshooting harder - can't directly access private instances**
❌ Requires bastion host or SSM for management access
❌ Potential single point of failure with NAT Gateway

**Mitigation Strategies:**
- Use AWS Systems Manager (SSM) Session Manager instead of bastion when possible
- Implement NAT Gateway in each AZ for redundancy (cost permitting)
- Use VPC Flow Logs for network troubleshooting
- Deploy bastion host in public subnet with strict security groups
- Enable detailed monitoring for NAT Gateway

**Constraints:**
- 📊 **Technical:** Private subnets require NAT Gateway or VPC endpoints for AWS API access
- 💰 **Cost:** NAT Gateway = $32/month + $0.045/GB data processing
- 📈 **Scalability:** Each AZ can have multiple public/private subnet pairs
- 🔒 **Security:** Network ACLs required for additional layer of security

**Why Not Other Options:**
- **Option A (All Public):** Security nightmare - every instance has public IP, direct exposure to internet. Violates principle of least privilege. Not suitable for production.
- **Option C (All Private):** Overkill for initial deployment - requires VPN/Direct Connect, complex setup, higher cost. Makes development and initial testing difficult. Good for highly regulated environments but adds unnecessary friction.

---

### Decision 3: NAT Gateway vs NAT Instance

**Problem Statement:**
How should we provide internet access to resources in private subnets for updates, patching, and external API calls?

**Options Considered:**
- **Option A:** NAT Gateway (AWS managed service)
- **Option B:** NAT Instance (self-managed EC2)
- **Option C:** VPC Endpoints for AWS services only

**Selection:**
**Option A: NAT Gateway (AWS managed service)**

**Reasoning:**
NAT Gateway is a fully managed AWS service that provides high availability (within an AZ) and bandwidth scaling automatically. While more expensive than NAT instances, it eliminates operational overhead and provides better reliability. For Stage 1, we'll deploy a single NAT Gateway in AZ-1 to optimize costs while learning the pattern.

**Pros:**
✅ **✅ Fully managed - no patching, maintenance, or monitoring required**
✅ **✅ High availability - automatically scales with bandwidth**
✅ **✅ Redundant within AZ - built-in redundancy**
✅ **✅ Simple to set up - minimal configuration**
✅ **✅ Predictable performance - no bandwidth contention**
✅ **✅ AWS native integration - works seamlessly with VPC**

**Cons:**
❌ **❌ Expensive - $32/month per gateway + $0.045/GB data processing**
❌ **❌ AZ-bound - must create one per AZ for true HA**
❌ **❌ Cannot control - cannot customize or configure**
❌ **❌ Potential bottleneck - single gateway for all private subnets in AZ**
❌ No cost controls - can't cap bandwidth or spending

**Mitigation Strategies:**
- Start with single NAT Gateway in AZ-1 for cost optimization
- Monitor data transfer costs with CloudWatch
- Add second NAT Gateway in AZ-2 if high availability required
- Use VPC endpoints for AWS services (S3, DynamoDB) to bypass NAT
- Implement cost alerts for NAT Gateway data processing

**Constraints:**
- 📊 **Technical:** Must be deployed in public subnet, requires Elastic IP
- 💰 **Cost:** $32/month per AZ + $0.045/GB data processing
- 📈 **Scalability:** Scales automatically to 45 Gbps
- 🔒 **Security:** Managed by AWS, no direct access

**Why Not Other Options:**
- **Option B (NAT Instance):** Operational burden - you must manage, patch, monitor, and scale it manually. Single point of failure unless configured with autoscaling. Bandwidth limited by instance size. Cost savings ($15-30/month) not worth the operational complexity for most use cases.
- **Option C (VPC Endpoints Only):** Too restrictive - only works for AWS services, doesn't provide general internet access needed for OS updates, external APIs, package repositories. Good optimization to combine with NAT Gateway, but not a complete replacement.

---

### Decision 4: Security Group Strategy

**Problem Statement:**
How should we organize security groups to provide appropriate access control while maintaining manageability?

**Options Considered:**
- **Option A:** Single security group for everything
- **Option B:** Tiered security groups by function (Web, App, DB)
- **Option C:** Granular security groups per resource

**Selection:**
**Option B: Tiered security groups by function**

**Reasoning:**
Tiered security groups align with the traditional three-tier architecture model. This approach provides clear separation of concerns - web tier allows public access, app tier allows web tier access, database tier allows only app tier access. It strikes the right balance between security and manageability.

**Pros:**
✅ **✅ Clear separation of concerns - each tier has specific access rules**
✅ **✅ Defense in depth - multiple layers of security controls**
✅ **✅ Easy to understand - logical grouping**
✅ **✅ Reusable - can be applied to multiple resources**
✅ **✅ Follows least privilege - minimal required access**
✅ **✅ Easy to audit - clear security boundaries**

**Cons:**
❌ **❌ More complex than single SG - requires careful planning**
❌ **❌ Potential rule explosion if too granular**
❌ **❌ Must manage SG dependencies - order matters**
❌ Requires documentation to maintain clarity
❌ Can be difficult to troubleshoot access issues

**Mitigation Strategies:**
- Document security group purposes and rules in design docs
- Use descriptive naming conventions (e.g., sg-web-frontend, sg-app-backend)
- Implement security group rules as Terraform modules
- Use security group referencing instead of CIDR blocks where possible
- Regular security audits to remove unused rules
- Consider security group management tools for complex environments

**Constraints:**
- 📊 **Technical:** Max 5 security groups per network interface, 60 rules per SG
- 💰 **Cost:** No additional cost for security groups
- 📈 **Scalability:** Can become complex with many microservices
- 🔒 **Security:** Stateful rules - return traffic automatically allowed

**Why Not Other Options:**
- **Option A (Single SG):** Security anti-pattern - all resources have same access level. Violates principle of least privilege. If one resource is compromised, attacker has access to everything. Makes auditing and compliance difficult.
- **Option C (Granular per Resource):** Management nightmare - hundreds of security groups become unmanageable. Difficult to understand relationships. Exceeds AWS limits (5 SGs per NIC). Only suitable for very large, mature organizations with automated security management.

**Security Groups Created:**
- **sg-web-frontend:** HTTP/HTTPS from internet (0.0.0.0/0)
- **sg-app-backend:** HTTP from web SG, SSH from bastion SG
- **sg-database:** Database port (5432/3306) from app SG only
- **sg-bastion:** SSH from specific IP ranges (can be restricted further)
- **sg-monitoring:** Allow monitoring agents (CloudWatch, etc.)

---

### Decision 5: IAM Strategy

**Problem Statement:**
How should we manage identity and access for EC2 instances to interact with AWS services (SSM, CloudWatch, S3, etc.)?

**Options Considered**
- **Option A:** Access keys and secret keys on instances
- **Option B:** IAM roles with instance profiles
- **Option C:** Resource-based policies only

**Selection:**
**Option B: IAM roles with instance profiles**

**Reasoning:**
IAM roles with instance profiles are the AWS-recommended approach for providing credentials to EC2 instances. They automatically rotate credentials, eliminate the need to store long-lived access keys, and follow the principle of least privilege. This is more secure and operationally simpler than managing access keys manually.

**Pros:**
✅ **✅ Automatic credential rotation - no manual key rotation required**
✅ **✅ No stored credentials - no keys in code or configuration files**
✅ **✅ Least privilege - grant only needed permissions**
✅ **✅ Easy to audit - CloudTrail logs all role activity**
✅ **✅ Revocable - can revoke access without redeploying instances**
✅ **✅ AWS best practice - recommended by AWS**
✅ Works seamlessly with AWS SDKs

**Cons:**
❌ **❌ Additional setup complexity - must create roles and policies**
❌ **❌ Cold start delay - slight delay when first assuming role**
❌ **❌ Requires instance profile association - can't be added later easily**
❌ **❌ Policy management overhead - must keep policies updated**
❌ Potential for permission errors if not configured correctly

**Mitigation Strategies:**
- Use Terraform modules to standardize role creation
- Start with minimal permissions and add as needed
- Implement IAM Access Analyzer to validate permissions
- Use AWS managed policies where appropriate
- Document role purposes and required permissions
- Test permissions in development environment first
- Use condition keys to restrict permissions further

**Constraints:**
- 📊 **Technical:** Max 10 roles per instance, one instance profile per instance
- 💰 **Cost:** No additional cost for IAM roles
- 📈 **Scalability:** Can manage thousands of roles with IAM
- 🔒 **Security:** Policies limited to 2048 characters for managed policies

**IAM Roles Created:**
- **ec2-instance-role:** Base role for application instances
  - ssm:StartSession - for Session Manager access
  - ssm:UpdateInstanceInformation - for SSM agent
  - ec2:DescribeTags - for instance identification
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents - for CloudWatch Logs
  - s3:GetObject - for accessing configuration from S3 (future)

**Why Not Other Options:**
- **Option A (Access Keys):** Security risk - long-lived credentials that must be manually rotated. If keys are compromised (in code repos, logs, etc.), attacker has persistent access. No automatic rotation. Violates security best practices.
- **Option C (Resource-Based Policies Only):** Not sufficient - resource policies control who can access the resource, but don't provide identity to the EC2 instance. Many AWS services require IAM permissions that can't be granted through resource policies alone. Doesn't provide the identity context needed for auditing.

---

### Decision 6: EC2 Instance Type Selection

**Problem Statement:**
Which EC2 instance type should we use for our initial deployment to balance cost, performance, and learning value?

**Options Considered:**
- **Option A:** t2.nano ($4.75/month) - minimal cost
- **Option B:** t3.micro ($7.59/month) - modern burstable
- **Option C:** t3.small ($15.25/month) - more capacity
- **Option D:** m5.large ($77/month) - consistent performance

**Selection:**
**Option B: t3.micro**

**Reasoning:**
The t3.micro is an excellent choice for Stage 1 infrastructure. It's part of the latest generation of burstable instances, providing a good balance of cost and performance for development and testing workloads. The t3 family uses the AWS Nitro system, providing better performance than older t2 instances. At $7.59/month, it's affordable for learning while providing enough capacity to run a web server and application server.

**Pros:**
✅ **✅ Cost-effective - $7.59/month for on-demand**
✅ **✅ Modern architecture - AWS Nitro system for better performance**
✅ **✅ Burstable performance - CPU credits for occasional spikes**
✅ **✅ Sufficient for development - 2 vCPU, 1 GB RAM**
✅ **✅ Learning value - real production-like instance type**
✅ **✅ Upgrade path - easy to move to t3.small/medium**
✅ **✅ Free tier eligible - 750 hours/month for first 12 months**

**Cons:**
❌ **❌ Limited resources - 1 GB RAM may be insufficient for some workloads**
❌ **❌ CPU credits can run out - performance drops if sustained high CPU**
❌ **❌ Not suitable for production - may be underpowered for real traffic**
❌ **❌ Limited networking - up to 5 Gbps only**
❌ EBS-optimized only on larger sizes

**Mitigation Strategies:**
- Monitor CPU credit balance with CloudWatch
- Use t3.unlimited to allow burst beyond baseline (for additional cost)
- Upgrade to t3.small or t3.medium if needed
- Use Auto Scaling to add instances when CPU is high
- Consider t3.medium for production deployments
- Optimize application for memory efficiency

**Constraints:**
- 📊 **Technical:** 2 vCPU, 1 GB RAM, up to 5 Gbps network
- 💰 **Cost:** $7.59/month on-demand, ~$3.75/month with 1-year reserved
- 📈 **Scalability:** Can upgrade to t3.small/medium, or move to m5/c5 family
- 🔒 **Security:** Supports nitro TPM, measured boot

**Instance Specifications:**
- **vCPU:** 2 (burstable)
- **Memory:** 1 GB
- **Network:** Up to 5 Gbps
- **Storage:** EBS only
- **CPU Credits:** 6 credits/hour baseline, earn 12/hour when idle
- **Use Cases:** Web servers, development environments, small databases

**Why Not Other Options:**
- **Option A (t2.nano):** Too limited - 1 vCPU, 512 MB RAM. Older generation (pre-Nitro). Not enough memory for modern web stacks. Only $3/month savings not worth the performance hit.
- **Option C (t3.small):** Overkill for Stage 1 - 2 GB RAM more than needed initially. Costs 2x as much. Better to start small and upgrade if needed.
- **Option D (m5.large):** Far too expensive for Stage 1 - $77/month is 10x the cost. Consistent performance not needed for development. Use this for production, not learning.

---

## 3. Cost Analysis

### Monthly Cost Breakdown (2 AZ Deployment)

| Component | Quantity | Unit Cost | Monthly Cost |
|-----------|----------|-----------|--------------|
| **VPC** | 1 | $0 | $0 |
| **Internet Gateway** | 1 | $0 | $0 |
| **NAT Gateway** | 1 | $32 | $32 |
| **NAT Data Processing** | 10 GB | $0.045/GB | $0.45 |
| **EC2 t3.micro** | 2 | $7.59 | $15.18 |
| **EBS Storage (gp3)** | 20 GB | $0.08/GB | $1.60 |
| **EBS IOPS** | 3,000 | $0.0025 | $7.50 |
| **EBS Throughput** | 125 MB | $0.004 | $0.50 |
| **Data Transfer Out** | 50 GB | $0.09/GB | $4.50 |
| **Elastic IPs** | 2 | $0.005/hr | $7.20 |
| **CloudWatch Logs** | 5 GB | $0.50/GB | $2.50 |
| **CloudWatch Metrics** | 10 | $0.30/metric | $3.00 |
| **SSM Session Manager** | 1 | $0 | $0 |
| **Route 53** | 1 | $0 | $0 |
| **Total** | | | **$74.43** |

### Cost Optimization Tips

1. **Use Reserved Instances:** Save ~40% by committing to 1-year term
   - t3.micro reserved: ~$4.50/month (vs $7.59 on-demand)
   - **Savings: $6.18/month**

2. **NAT Gateway Optimization:**
   - Use VPC endpoints for S3 and DynamoDB to bypass NAT
   - Add NAT Gateway to second AZ only if high availability required
   - **Savings: $5-10/month with VPC endpoints**

3. **EBS Storage:**
   - Use gp2 instead of gp3 for lower storage requirements
   - Delete unattached volumes regularly
   - **Savings: $2-5/month**

4. **Data Transfer:**
   - Use CloudFront for static content
   - Enable S3 Transfer Acceleration only when needed
   - **Savings: Varies by usage**

5. **CloudWatch Optimization:**
   - Set reasonable retention periods (don't keep logs forever)
   - Use CloudWatch Logs Insights instead of exporting to S3
   - **Savings: $1-3/month**

**Optimized Monthly Cost: ~$55-60/month** (~20% savings)

### Cost Comparison with Alternative Architectures

| Architecture | Monthly Cost | Savings |
|--------------|--------------|---------|
| Single AZ | $50 | -$24 (33%) |
| 2 AZ (Current) | $74 | - |
| 3 AZ | $110 | +$36 (49%) |
| With NAT in both AZs | $106 | +$32 (43%) |

---

## 4. Security Considerations

### Network Security

**VPC Design:**
- ✅ Private subnets for application servers - no direct internet access
- ✅ Public subnets only for internet-facing resources (ALB, Bastion)
- ✅ Network ACLs as second layer of defense (stateless)
- ✅ VPC Flow Logs enabled for network monitoring
- ✅ Security groups follow least privilege principle

**Security Group Rules:**
- **Web Tier:** HTTP/HTTPS from internet only
- **App Tier:** HTTP from Web tier only, SSH from Bastion only
- **Database Tier:** Database port from App tier only
- **Bastion:** SSH from specific IP ranges (can be restricted)
- **Monitoring:** Allow required monitoring ports

**Encryption:**
- ✅ EBS volumes encrypted by default
- ✅ Data in transit between AZs encrypted
- ✅ TLS/SSL for all public endpoints
- ✅ SSH key-based authentication only

### Access Control

**IAM Strategy:**
- ✅ No access keys on instances - use IAM roles
- ✅ Instance profiles with minimal required permissions
- ✅ Separate IAM roles for different instance types
- ✅ Regular permission audits using IAM Access Analyzer
- ✅ MFA required for console access

**SSH Access:**
- ✅ Bastion host for SSH access (can be replaced with SSM)
- ✅ SSH keys only - no password authentication
- ✅ Key rotation every 90 days
- ✅ Consider AWS Systems Manager Session Manager (no bastion needed)

**Management Access:**
- ✅ AWS Organization with service control policies (future)
- ✅ Separate IAM users for each team member
- ✅ CloudTrail enabled for API logging
- ✅ Config rules for compliance checking (future)

### Data Protection

**At Rest:**
- ✅ EBS encryption enabled
- ✅ S3 bucket encryption (when used)
- ✅ RDS encryption (when deployed)
- ✅ Parameter Store KMS encryption (future)

**In Transit:**
- ✅ HTTPS for all public endpoints
- ✅ TLS for database connections
- ✅ VPC encryption within AWS network

**Backup and Recovery:**
- ✅ EBS snapshots (automated)
- ✅ Cross-AZ replication for critical data
- ✅ Disaster recovery plan documented

### Monitoring and Logging

**CloudWatch Metrics:**
- CPU utilization
- Memory utilization (requires agent)
- Disk I/O
- Network I/O
- Status checks

**CloudWatch Logs:**
- Application logs
- System logs (/var/log)
- Security logs (auth.log, secure)
- VPC Flow Logs

**Alerting:**
- NAT Gateway data processing anomalies
- EC2 instance health checks
- Security group rule changes
- IAM policy changes

**Additional Monitoring:**
- AWS GuardDuty for threat detection (future)
- AWS Security Hub for compliance (future)
- AWS Config for configuration tracking (future)

---

## 5. Alternatives Considered

### Why Terraform vs AWS CDK?

**Chosen: Terraform**

**Reasoning:**
- **Declarative approach:** Terraform's state-based approach is ideal for infrastructure
- **Provider support:** Works with AWS, GCP, Azure - vendor neutral
- **Maturity:** Larger community, more examples, battle-tested
- **Learning value:** Better for understanding infrastructure concepts
- **State management:** Clear understanding of infrastructure state
- **Team skills:** Easier to find developers with Terraform experience

**AWS CDK Trade-offs:**
- ✅ Pros: Programming language (TypeScript, Python), abstractions, constructs
- ❌ Cons: AWS-specific, steeper learning curve, less mature, less predictable

**When to consider CDK:**
- Team already knows TypeScript/Python well
- Need complex infrastructure abstractions
- Building custom constructs for reuse
- AWS-only deployment

### Why Terraform vs AWS CloudFormation?

**Chosen: Terraform**

**Reasoning:**
- **Multi-cloud:** Can use same tooling across cloud providers
- **State management:** Terraform state is more transparent
- **Community:** Larger ecosystem of modules and providers
- **Drift detection:** Better drift detection and remediation
- **Language:** HCL is more readable than YAML/JSON for infrastructure

**CloudFormation Trade-offs:**
- ✅ Pros: AWS-native, direct integration, no state file, AWS support
- ❌ Cons: YAML/JSON verbose, limited to AWS, stack limits, slower

**When to consider CloudFormation:**
- AWS-only deployment
- Need AWS support directly
- Already using AWS StackSets
- Prefer YAML over HCL

### Why Not Serverless for Stage 1?

**Decision: Use EC2 for Stage 1, consider serverless for Stage 2+**

**Reasoning for EC2 in Stage 1:**
- **Learning value:** Better understanding of networking, OS, security
- **Visibility:** Can see and touch all components
- **Debugging:** Easier to troubleshoot issues
- **Control:** Full control over environment
- **Cost:** Predictable costs, easier to estimate
- **Skills:** Builds foundational cloud infrastructure skills

**Serverless Trade-offs:**
- ✅ Pros: No server management, auto-scaling, pay-per-use, lower operational burden
- ❌ Cons: Abstraction hides details, cold starts, vendor lock-in, harder debugging

**When to consider serverless (Stage 2+):**
- Application is event-driven or sporadic workloads
- Need rapid auto-scaling
- Want to reduce operational overhead
- Cost optimization for variable workloads
- API Gateway + Lambda for REST APIs
- App Runner for containerized applications

**Serverless options for future stages:**
- **API Gateway + Lambda:** REST APIs, event processing
- **App Runner:** Containerized web applications
- **Fargate:** Container orchestration without server management
- **Lambda with EFS:** Stateful applications

---

## 6. Lessons Learned

### What Works Well

**1. Hybrid Public/Private Architecture**
- Provides excellent security posture
- Follows AWS best practices
- Scales well as application grows
- Cost-effective with single NAT Gateway

**2. Terraform Modules**
- Reusable infrastructure patterns
- Consistent deployments across environments
- Easier to maintain and update
- Good for team collaboration

**3. IAM Roles with Instance Profiles**
- No credential management needed
- Automatic rotation
- Least privilege permissions
- Easy to audit

**4. Security Groups by Function**
- Clear security boundaries
- Easy to understand access patterns
- Simple to audit and troubleshoot
- Follows defense-in-depth principle

**5. CloudWatch Monitoring**
- Integrated monitoring and alerting
- No additional agents required
- Centralized logs
- Metric-based auto-scaling

### Potential Improvements

**1. Add Third NAT Gateway for High Availability**
- Current: Single NAT Gateway is single point of failure
- Improvement: Add NAT Gateway to second AZ
- Trade-off: Additional $32/month cost
- Recommendation: Add when moving to production

**2. Implement Multi-Region Deployment**
- Current: Single region deployment
- Improvement: Deploy to second region for disaster recovery
- Trade-off: 2x infrastructure cost, increased complexity
- Recommendation: Consider after single-region is stable

**3. Add Application Load Balancer**
- Current: Direct access to EC2 instances
- Improvement: Add ALB for better traffic distribution
- Trade-off: Additional $18/month cost
- Recommendation: Add when scaling beyond 2 instances

**4. Use Auto Scaling Groups**
- Current: Fixed number of instances
- Improvement: Replace with ASG for automatic scaling
- Trade-off: Additional configuration complexity
- Recommendation: Implement before production deployment

**5. Implement Infrastructure Testing**
- Current: Manual testing
- Improvement: Use Terratest for automated testing
- Trade-off: Additional testing infrastructure
- Recommendation: Add before production deployment

**6. Add GitOps with Terraform Cloud**
- Current: Local Terraform execution
- Improvement: Use Terraform Cloud for remote state and execution
- Trade-off: Additional tool and potential cost
- Recommendation: Consider for team collaboration

### Common Pitfalls to Avoid

**1. Forgetting to Destroy Resources**
- ⚠️ EBS volumes, snapshots, and Elastic IPs continue charging after `terraform destroy`
- **Solution:** Always verify resource cleanup, use `aws ec2 describe-volumes`

**2. NAT Gateway Cost Surprise**
- ⚠️ $32/month per NAT Gateway + data processing charges
- **Solution:** Monitor costs, use VPC endpoints for AWS services

**3. Security Group Rule Explosion**
- ⚠️ Too many rules become unmanageable
- **Solution:** Use security group references instead of CIDR blocks, document rules

**4. Hard-Coded Values in Terraform**
- ⚠️ Difficult to change and maintain
- **Solution:** Use variables, locals, and modules effectively

**5. Ignoring State File Management**
- ⚠️ Lost state file = lost infrastructure tracking
- **Solution:** Use remote state (S3 + DynamoDB), backup state file

**6. Not Testing Destroy Process**
- ⚠️ Resources with `prevent_destroy` or dependencies can't be destroyed
- **Solution:** Test destroy in development environment first

**7. Under-Provisioning Instances**
- ⚠️ t3.micro may be too small for production workloads
- **Solution:** Monitor CPU credits and performance, upgrade when needed

**8. Forgetting to Tag Resources**
- ⚠️ Difficult to track costs and ownership
- **Solution:** Implement consistent tagging strategy from the start

**9. Not Planning for Data Transfer Costs**
- ⚠️ Data transfer out can be expensive
- **Solution:** Use CloudFront, compress data, cache responses

**10. Ignoring the Free Tier**
- ⚠️ Missing out on 750 hours/month of EC2 for first year
- **Solution:** Use t2/t3 micro instances to maximize free tier benefits

### Best Practices for Next Stages

1. **Start Small:** Always begin with minimal resources and scale up
2. **Monitor Everything:** You can't optimize what you don't measure
3. **Document Decisions:** Write down why you made specific choices
4. **Test Destroy:** Always test that you can cleanly destroy infrastructure
5. **Use Modules:** Reuse infrastructure patterns across environments
6. **Automate Testing:** Use Terratest or similar for infrastructure testing
7. **Cost Alerts:** Set up billing alerts to avoid surprises
8. **Security First:** Apply security controls from the start, not as an afterthought
9. **Backup State:** Keep multiple copies of Terraform state file
10. **Review Regularly:** Architecture should evolve with requirements

---

## Summary

This Stage 1 architecture provides a solid foundation for cloud infrastructure learning and development. The decisions documented here balance cost, security, scalability, and learning value while following AWS best practices.

**Key Takeaways:**
- 2-AZ architecture provides high availability without excessive cost
- Hybrid public/private subnet design follows defense-in-depth
- NAT Gateway simplifies operations but adds cost
- Tiered security groups provide clear access boundaries
- IAM roles are superior to access keys for instance permissions
- t3.micro instances are cost-effective for development

**Monthly Cost:** ~$74 (can be optimized to ~$55-60)

**Next Steps:**
1. Deploy and test the infrastructure
2. Implement monitoring and alerting
3. Add application load balancer
4. Set up CI/CD pipeline
5. Plan for Stage 2 enhancements

---

**Design Document Created:** 2026-03-10
**Author:** Terraform Foundation Stage 1
**Version:** 1.0
**Status:** Ready for Implementation

**Next:** Deploy and test the infrastructure

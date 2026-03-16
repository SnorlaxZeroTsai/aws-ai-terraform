# Agent 智慧：從 Chatbot 到 Autonomous Agent

**學習目標：** 理解 Agent 的核心概念，掌握 ReAct 模式和 Tool Use

---

## 回顧：從 Stage 2 到 Stage 5

**Stage 2（Chatbot）：**
```
[用戶問題] → [LLM] → [回答]

能力：
✅ 對話
✅ 問答
❌ 無法執行任務
❌ 無法使用工具
```

**Stage 4（RAG）：**
```
[用戶問題] → [檢索] → [LLM + 上下文] → [回答]

能力：
✅ 對話
✅ 問答
✅ 使用知識庫
❌ 無法執行任務
❌ 無法使用工具
```

**Stage 5（Agent）：**
```
[用戶問題] → [Agent]
    ↓
[推理 + 規劃]
    ↓
[選擇工具]
    ↓
[執行任務]
    ↓
[觀察結果]
    ↓
[決定下一步]

能力：
✅ 對話
✅ 問答
✅ 使用知識庫
✅ 執行任務
✅ 使用工具
✅ 多步推理
```

---

## 什麼是 Agent？

### 定義

**Agent = 能自主感知和行動的系統**

```
核心特點：
1. 感知（Perception）→ 觀察環境
2. 推理（Reasoning）→ 規劃行動
3. 行動（Action）→ 執行任務
4. 記憶（Memory）→ 記住經驗
```

### 簡單 Agent vs 自主 Agent

**簡單 Agent（Stage 2 Chatbot）：**
```
[輸入] → [LLM] → [輸出]

特點：
→ 被動回應
→ 無記憶
→ 無工具
→ 單次互動
```

**自主 Agent（Stage 5）：**
```
[目標]
    ↓
[觀察環境]
    ↓
[規劃步驟]
    ↓
[執行 → 觀察 → 調整]
    ↓
[完成目標]

特點：
→ 主動規劃
→ 有記憶
→ 使用工具
→ 多步互動
```

---

## ReAct 模式

### 核心概念

**ReAct = Reasoning + Acting**

```
傳統 LLM：
問題 → 思考 → 答案

ReAct：
問題 → 思考 → 行動 → 觀察 → 思考 → 行動 → ...
                       ↑_______循環_____↑
```

### 流程範例

```
用戶：「AWS 上有哪些可用的 GPU 實例？」

Thought 1：用戶想知道 AWS GPU 實例
Action 1：搜尋 AWS 文件
Observation 1：找到 p3, p4, g4dn 等系列

Thought 2：需要最新的定價資訊
Action 2：查詢定價頁面
Observation 2：p3.2xlarge 是 $3.06/hour

Thought 3：現在可以回答了
Action 3：回應用戶
Answer：AWS 有 p3、p4、g4dn 等系列...
```

### 為什麼 ReAct 重要？

**解決 LLM 的限制：**
```
❌ LLM 只能訓練時的知識
❌ LLM 無法執行任務
❌ LLM 無法存取即時資訊

✅ ReAct 解決：
→ 可以使用工具
→ 可以存取即時資訊
→ 可以執行真實任務
```

---

## Tool Use（工具使用）

### 什麼是 Tool？

**Tool = Agent 可以使用的函數/服務**

```
常用工具類別：

1. 搜尋工具
   → Google Search
   → Wikipedia
   → 內部知識庫

2. 資料庫工具
   → SQL Query
   → DynamoDB Query
   → Vector Search

3. API 工具
   → REST API
   → GraphQL
   → Webhooks

4. 計算工具
   → Calculator
   → Code Interpreter
   → Data Analysis
```

### Tool 定義範例

```python
# 工具定義
tools = [
    {
        "name": "search_database",
        "description": "Search the company database for product information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "description": "Product category to filter"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_pricing",
        "description": "Get current pricing for AWS services",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "AWS service name (e.g., EC2, S3)"
                },
                "region": {
                    "type": "string",
                    "description": "AWS region"
                }
            },
            "required": ["service"]
        }
    }
]
```

### Tool 執行範例

```python
def execute_tool(tool_name, parameters):
    """執行工具"""
    if tool_name == "search_database":
        return search_database(parameters['query'])

    elif tool_name == "get_pricing":
        return get_pricing(
            service=parameters['service'],
            region=parameters.get('region', 'us-east-1')
        )

    else:
        return f"Error: Unknown tool {tool_name}"

# 使用範例
result = execute_tool("get_pricing", {"service": "EC2", "region": "us-east-1"})
print(result)  # {"instance": "t3.micro", "price": "$0.0084/hour"}
```

---

## Agent 記憶系統

### 為什麼需要記憶？

**沒有記憶的問題：**
```
[第一輪]
用戶：「我的 EC2 實例 ID 是 i-123」
Agent：「好的，我記住了」

[第二輪]
用戶：「那個實例的狀態是什麼？」
Agent：「哪個實例？」

→ Agent 忘記了之前的對話
```

### 記憶的層級

**1. 短期記憶（Conversation Memory）**
```
範圍：當前對話
存儲：Lambda 記憶體或 DynamoDB
壽命：對話結束後清除

用途：
→ 維持對話上下文
→ 記住對話中的關鍵資訊
```

**2. 長期記憶（Knowledge Base）**
```
範圍：所有對話
存儲：向量資料庫
壽命：永久

用途：
→ 記住用戶偏好
→ 學習使用者行為
→ 累積知識
```

**3. 工作記憶（Working Memory）**
```
範圍：當前任務
存儲：Step Functions 狀態
壽命：任務完成後清除

用途：
→ 追蹤任務進度
→ 儲存中間結果
→ 管理多步任務
```

### 實作範例

```python
class AgentMemory:
    def __init__(self):
        self.short_term = []  # 當前對話
        self.working = {}     # 當前任務
        self.long_term = None # 向量資料庫（連接）

    def remember(self, key, value, memory_type='short'):
        """儲存記憶"""
        if memory_type == 'short':
            self.short_term.append({key: value})
        elif memory_type == 'working':
            self.working[key] = value
        elif memory_type == 'long':
            # 儲存到向量資料庫
            self.long_term.store(key, value)

    def recall(self, query, memory_type='short'):
        """檢索記憶"""
        if memory_type == 'short':
            # 從短期記憶搜尋
            return [item for item in self.short_term if query in item]
        elif memory_type == 'working':
            # 從工作記憶取得
            return self.working.get(query)
        elif memory_type == 'long':
            # 從向量資料庫搜尋
            return self.long_term.search(query)

# 使用
memory = AgentMemory()
memory.remember('instance_id', 'i-123', 'short')
instance = memory.recall('instance_id')
```

---

## Step Functions 協調

### 為什麼需要 Step Functions？

**問題：Agent 可能很複雜**
```
[任務：查詢 EC2 實例狀態]
    ↓
[步驟 1：取得實例列表]
    ↓
[步驟 2：過濾特定實例]
    ↓
[步驟 3：取得狀態]
    ↓
[步驟 4：整理結果]
    ↓
[步驟 5：回應用戶]

每個步驟可能失敗
→ 需要重試
→ 需要錯誤處理
→ 需要狀態管理
```

**Step Functions 的優勢：**
```
✅ 視覺化工作流程
✅ 自動重試
✅ 錯誤處理
✅ 狀態管理
✅ 長時間執行（> 15 分鐘）
```

### 狀態機定義

```python
# Step Functions 狀態機定義
definition = {
    "Comment": "Agent workflow",
    "StartAt": "PlanAction",
    "States": {
        "PlanAction": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:planner",
            "Next": "ExecuteTool"
        },
        "ExecuteTool": {
            "Type": "Choice",
            "Choices": [{
                "Variable": "$.tool_type",
                "StringEquals": "search",
                "Next": "SearchTool"
            }, {
                "Variable": "$.tool_type",
                "StringEquals": "database",
                "Next": "DatabaseTool"
            }],
            "Default": "RespondToUser"
        },
        "SearchTool": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:search_tool",
            "Next": "ObserveResult"
        },
        "DatabaseTool": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:database_tool",
            "Next": "ObserveResult"
        },
        "ObserveResult": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:observer",
            "Next": "CheckCompletion"
        },
        "CheckCompletion": {
            "Type": "Choice",
            "Choices": [{
                "Variable": "$.completed",
                "BooleanEquals": false,
                "Next": "PlanAction"
            }],
            "Default": "RespondToUser"
        },
        "RespondToUser": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:responder",
            "End": True
        }
    }
}
```

---

## 實際範例

### 完整 Agent 循環

```python
class ReActAgent:
    def __init__(self, tools, memory):
        self.tools = tools
        self.memory = memory

    def run(self, user_query):
        """執行 Agent 循環"""
        # 初始化觀察
        observation = user_query

        # 最多執行 10 輪
        for iteration in range(10):
            # 1. 推理（Reasoning）
            thought = self.reason(observation)
            print(f"Thought {iteration}: {thought}")

            # 2. 判斷是否完成
            if self.is_complete(thought):
                return self.generate_answer(observation)

            # 3. 選擇行動（Acting）
            action = self.decide_action(thought)
            print(f"Action {iteration}: {action['name']}")

            # 4. 執行工具
            result = self.execute_tool(action)
            print(f"Observation {iteration}: {result}")

            # 5. 更新觀察
            observation = result

            # 6. 儲存記憶
            self.memory.remember(
                f"step_{iteration}",
                {"action": action, "result": result}
            )

    def reason(self, observation):
        """推理階段"""
        prompt = f"""
Based on the following observation, determine the next step:

Observation: {observation}

Available tools:
{json.dumps(self.tools, indent=2)}

Previous steps:
{self.memory.recall('steps')}

Think step by step:
1. What do I need to find out?
2. Which tool can help?
3. What should I do next?

Respond in format:
Thought: [your reasoning]
Action: [tool name]
Action Input: [tool parameters]
"""
        # 呼叫 LLM
        response = self.call_llm(prompt)
        return self.parse_response(response)

    def execute_tool(self, action):
        """執行工具"""
        tool_name = action['name']
        parameters = action['parameters']

        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return tool.execute(**parameters)
        else:
            return f"Error: Unknown tool {tool_name}"
```

---

## 成本考量

### 成本結構

```
Lambda 執行：
→ 每個 Tool 呼叫一次 Lambda
→ 10 次迭代 = 10 次 Lambda 呼叫
→ 成本：10 × $0.0001 = $0.001

LLM 呼叫：
→ 每次 Reasoning 都要呼叫 LLM
→ 10 次迭代 = 10 次 LLM 呼叫
→ 成本：10 × $0.003 = $0.03

Step Functions：
→ 每次轉換都收費
→ 10 個步驟 = 10 次轉換
→ 成本：10 × $0.000025 = $0.00025

總計：~$0.031 per query
```

### 優化策略

**1. 限制迭代次數**
```python
MAX_ITERATIONS = 5  # 從 10 降到 5
→ 節省 50% 成本
```

**2. 使用快取**
```python
# 快取常用工具結果
if query in cache:
    return cache[query]
```

**3. 減少 Prompt 長度**
```python
# 只包含必要的上下文
relevant_memory = self.memory.recall(query, top_k=3)
→ 減少 token 使用
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋 Agent 是什麼嗎？
- [ ] 我理解 ReAct 模式嗎？
- [ ] 我知道 Tool Use 的價值嗎？

**系統設計：**
- [ ] 我能設計 Agent 記憶系統嗎？
- [ ] 我知道如何使用 Step Functions 嗎？
- [ ] 我能設計多步推理流程嗎？

**實作能力：**
- [ ] 我能實作 ReAct 循環嗎？
- [ ] 我能定義和使用 Tool 嗎？
- [ ] 我能優化 Agent 成本嗎？

---

## 下一階段

完成 Stage 5 後，你會理解：
- ✅ Agent 的核心概念
- ✅ ReAct 模式的實作
- ✅ Tool Use 的設計
- ✅ 記憶系統的架構
- ✅ Step Functions 協調

**最後一階段：** Agent Platform（整合所有 Stage）

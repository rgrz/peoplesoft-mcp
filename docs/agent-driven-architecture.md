# Agent-Driven HR System Architecture

**"Business Rules as Data, Agents as the Runtime"**

A next-generation architecture for HR/HCM systems where business logic is stored as declarative data and AI agents interpret and execute that logic at runtime.

---

## Table of Contents

1. [Vision](#vision)
2. [Core Principles](#core-principles)
3. [Architecture Overview](#architecture-overview)
4. [Business Logic Data Model](#business-logic-data-model)
5. [Rule Extraction from PeopleSoft](#rule-extraction-from-peoplesoft)
6. [Agent Architecture](#agent-architecture)
7. [Regulatory Compliance Agent](#regulatory-compliance-agent)
8. [Multi-Jurisdiction Handling](#multi-jurisdiction-handling)
9. [Execution Flow](#execution-flow)
10. [Performance Considerations](#performance-considerations)
11. [Security Model](#security-model)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Technology Stack](#technology-stack)

---

## Vision

Traditional HR systems embed business logic in code (PeopleCode, Java, COBOL). This creates several problems:

- **Regulatory changes require code deployments** - A simple tax table update needs developers
- **Logic is opaque** - Business rules are buried in thousands of lines of code
- **Testing is expensive** - Every change requires QA cycles
- **Multi-jurisdiction is complex** - Federal/state/local rules become spaghetti code
- **Audit is difficult** - Explaining "why did the system do X?" requires code archaeology

**The Agent-Driven Architecture inverts this:**

- Business rules are **data**, stored in a database
- AI agents **read and execute** the rules at runtime
- Regulatory changes become **data updates**, not code deployments
- Rules are **explainable** - the agent can cite exactly which rule fired and why
- Rules are **auditable** - every change is versioned with source citations

---

## Core Principles

### 1. Rules are Data, Not Code

```
Traditional:
  if employee.state == "CA" and employee.hours > 8:
      overtime_rate = 1.5  # CA daily overtime

Agent-Driven:
  {
    "rule": "CA Daily Overtime",
    "condition": {"state": "CA", "daily_hours": {"gt": 8}},
    "action": {"set": "overtime_multiplier", "value": 1.5},
    "source": "CA Labor Code Section 510"
  }
```

### 2. Agents Interpret, Don't Hardcode

The agent reads rules and applies them contextually. It can:
- Determine which rules apply to a given situation
- Resolve conflicts between overlapping rules
- Explain its reasoning in natural language
- Adapt to new rules without code changes

### 3. Humans Approve, Agents Propose

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Regulation │────▶│    Agent    │────▶│   Human     │
│  Change     │     │  (proposes) │     │  (approves) │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │    Rule     │
                                        │  Database   │
                                        └─────────────┘
```

### 4. Everything is Auditable

Every rule execution logs:
- Which rule fired
- What conditions were evaluated
- What data was examined
- What action was taken
- Source citation for the rule

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Web UI  │  │   API    │  │ Chatbot  │  │  Batch   │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
└───────┼─────────────┼─────────────┼─────────────┼────────────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATION LAYER                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Transaction Agent                           │ │
│  │  • Receives request (hire, transfer, terminate, etc.)          │ │
│  │  • Loads applicable rules from Rule Database                   │ │
│  │  • Evaluates conditions against current data                   │ │
│  │  • Executes actions (validations, defaults, calculations)      │ │
│  │  • Returns result with explanation                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │    TOOLS    │     │   SKILLS    │     │    RULES    │           │
│  │             │     │             │     │  (Agent     │           │
│  │ query_data  │     │ hr_domain   │     │  Guardrails)│           │
│  │ save_record │     │ tax_calc    │     │             │           │
│  │ get_rules   │     │ compliance  │     │ audit_all   │           │
│  │ eval_cond   │     │ eff_dating  │     │ validate    │           │
│  │ exec_action │     │             │     │ security    │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
└──────────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     RULE     │     │ OPERATIONAL  │     │    AUDIT     │
│   DATABASE   │     │   DATABASE   │     │     LOG      │
│              │     │              │     │              │
│ • Entities   │     │ • Employees  │     │ • Who        │
│ • Attributes │     │ • Jobs       │     │ • What       │
│ • Rules      │     │ • Payroll    │     │ • When       │
│ • Conditions │     │ • Benefits   │     │ • Why (rule) │
│ • Actions    │     │              │     │ • Source     │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Business Logic Data Model

### Core Schema

```sql
-- ============================================================
-- ENTITIES: The business objects in the system
-- ============================================================
CREATE TABLE bl_entities (
    entity_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_name         VARCHAR(100) NOT NULL UNIQUE,  -- 'Employee', 'Job', 'PayrollRun'
    entity_description  TEXT,
    source_system       VARCHAR(50),                   -- 'PeopleSoft', 'Manual', 'Regulation'
    source_record       VARCHAR(30),                   -- PS_JOB, PS_PERSONAL_DATA
    effective_dated     BOOLEAN DEFAULT FALSE,
    key_fields          JSONB,                         -- ["EMPLID", "EMPL_RCD", "EFFDT"]
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ATTRIBUTES: Properties of entities
-- ============================================================
CREATE TABLE bl_attributes (
    attribute_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES bl_entities(entity_id),
    attribute_name      VARCHAR(100) NOT NULL,         -- 'annual_salary', 'hire_date'
    attribute_label     VARCHAR(200),                  -- 'Annual Salary', 'Hire Date'
    data_type           VARCHAR(30) NOT NULL,          -- 'string', 'decimal', 'date', 'boolean', 'integer'
    source_field        VARCHAR(30),                   -- ANNUAL_RT (from PeopleSoft)
    is_required         BOOLEAN DEFAULT FALSE,
    is_derived          BOOLEAN DEFAULT FALSE,         -- Calculated field
    derivation_rule_id  UUID,                          -- Link to calculation rule
    translate_field     VARCHAR(30),                   -- For XLAT lookups
    default_value       JSONB,
    validation_rules    JSONB,                         -- Inline simple validations
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_id, attribute_name)
);

-- ============================================================
-- RULES: The business logic
-- ============================================================
CREATE TABLE bl_rules (
    rule_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code           VARCHAR(50) UNIQUE,            -- 'TAX-FED-WITHHOLD-2026'
    rule_name           VARCHAR(200) NOT NULL,
    rule_description    TEXT,
    rule_type           VARCHAR(50) NOT NULL,          -- See rule types below
    category            VARCHAR(100),                  -- 'Tax', 'Benefits', 'Leave', 'Validation'
    entity_id           UUID REFERENCES bl_entities(entity_id),
    trigger_event       VARCHAR(100),                  -- 'on_save', 'on_change:DEPTID', 'scheduled'
    priority            INTEGER DEFAULT 100,           -- Lower = higher priority
    effective_date      DATE,                          -- When rule becomes active
    expiration_date     DATE,                          -- When rule expires (null = no expiry)
    jurisdiction        VARCHAR(50),                   -- 'US', 'US-CA', 'US-CA-SF'
    source_document     VARCHAR(500),                  -- 'IRS Publication 15-T (2026)'
    source_url          VARCHAR(1000),
    source_section      VARCHAR(200),                  -- 'Table 1, Page 12'
    source_system       VARCHAR(100),                  -- 'PeopleSoft:JOB.DEPTID.FieldChange'
    is_active           BOOLEAN DEFAULT TRUE,
    requires_approval   BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    created_by          VARCHAR(100),
    approved_by         VARCHAR(100),
    approved_at         TIMESTAMP
);

-- Rule Types:
-- • 'validation'    - Check data validity, return errors/warnings
-- • 'default'       - Set default values
-- • 'calculation'   - Compute derived values
-- • 'workflow'      - Trigger approvals or notifications
-- • 'eligibility'   - Determine if something applies
-- • 'rate_table'    - Tax brackets, contribution limits
-- • 'mapping'       - Transform values (code → description)

-- ============================================================
-- RULE CONDITIONS: When does the rule apply?
-- ============================================================
CREATE TABLE bl_rule_conditions (
    condition_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID NOT NULL REFERENCES bl_rules(rule_id) ON DELETE CASCADE,
    condition_group     INTEGER DEFAULT 1,             -- For grouping AND/OR logic
    condition_seq       INTEGER NOT NULL,
    logic_operator      VARCHAR(10) DEFAULT 'AND',     -- 'AND', 'OR'
    attribute_path      VARCHAR(200) NOT NULL,         -- 'employee.job.hr_status'
    operator            VARCHAR(30) NOT NULL,          -- See operators below
    operand_type        VARCHAR(20) DEFAULT 'literal', -- 'literal', 'reference', 'function'
    operand_value       JSONB,                         -- Value to compare against
    description         TEXT,
    UNIQUE(rule_id, condition_group, condition_seq)
);

-- Operators:
-- • 'equals', 'not_equals'
-- • 'greater_than', 'greater_than_or_equal'
-- • 'less_than', 'less_than_or_equal'
-- • 'in_list', 'not_in_list'
-- • 'is_null', 'is_not_null'
-- • 'contains', 'starts_with', 'ends_with'
-- • 'between', 'not_between'
-- • 'matches_regex'

-- ============================================================
-- RULE ACTIONS: What does the rule do?
-- ============================================================
CREATE TABLE bl_rule_actions (
    action_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID NOT NULL REFERENCES bl_rules(rule_id) ON DELETE CASCADE,
    action_seq          INTEGER NOT NULL,
    action_type         VARCHAR(50) NOT NULL,          -- See action types below
    target_path         VARCHAR(200),                  -- 'employee.job.reports_to'
    value_type          VARCHAR(20) DEFAULT 'literal', -- 'literal', 'reference', 'expression', 'lookup'
    value_expression    JSONB,                         -- The value or expression
    error_code          VARCHAR(50),
    error_message       TEXT,
    error_severity      VARCHAR(20),                   -- 'error', 'warning', 'info'
    description         TEXT,
    UNIQUE(rule_id, action_seq)
);

-- Action Types:
-- • 'set_value'       - Set a field value
-- • 'error'           - Raise validation error (blocks save)
-- • 'warning'         - Raise warning (allows save)
-- • 'create_record'   - Create a related record
-- • 'update_record'   - Update a related record
-- • 'delete_record'   - Delete a related record
-- • 'call_service'    - Invoke external service
-- • 'send_notification' - Email, SMS, in-app notification
-- • 'start_workflow'  - Initiate approval workflow
-- • 'log_event'       - Write to audit log

-- ============================================================
-- RULE EXPRESSIONS: Complex calculations
-- ============================================================
CREATE TABLE bl_rule_expressions (
    expression_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID NOT NULL REFERENCES bl_rules(rule_id) ON DELETE CASCADE,
    expression_name     VARCHAR(100),
    expression_type     VARCHAR(50) NOT NULL,          -- 'formula', 'lookup', 'aggregate', 'conditional'
    expression_text     TEXT NOT NULL,                 -- 'base_salary * (1 + merit_pct / 100)'
    input_parameters    JSONB,                         -- Parameter definitions
    return_type         VARCHAR(30),                   -- 'decimal', 'string', 'date', etc.
    description         TEXT
);

-- ============================================================
-- RATE TABLES: Tax brackets, limits, tiers
-- ============================================================
CREATE TABLE bl_rate_tables (
    table_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID NOT NULL REFERENCES bl_rules(rule_id) ON DELETE CASCADE,
    table_name          VARCHAR(100) NOT NULL,
    effective_date      DATE NOT NULL,
    expiration_date     DATE,
    jurisdiction        VARCHAR(50),
    filing_status       VARCHAR(50),                   -- 'single', 'married_joint', etc.
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bl_rate_table_rows (
    row_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id            UUID NOT NULL REFERENCES bl_rate_tables(table_id) ON DELETE CASCADE,
    row_seq             INTEGER NOT NULL,
    lower_bound         DECIMAL(15,2),
    upper_bound         DECIMAL(15,2),
    rate                DECIMAL(10,6),                 -- 0.22 for 22%
    flat_amount         DECIMAL(15,2),                 -- Base amount
    additional_fields   JSONB,                         -- Flexible extra columns
    UNIQUE(table_id, row_seq)
);

-- ============================================================
-- WORKFLOWS: Multi-step approval and routing
-- ============================================================
CREATE TABLE bl_workflows (
    workflow_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_code       VARCHAR(50) UNIQUE,
    workflow_name       VARCHAR(200) NOT NULL,
    workflow_description TEXT,
    trigger_entity_id   UUID REFERENCES bl_entities(entity_id),
    trigger_event       VARCHAR(100),
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bl_workflow_steps (
    step_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id         UUID NOT NULL REFERENCES bl_workflows(workflow_id) ON DELETE CASCADE,
    step_seq            INTEGER NOT NULL,
    step_name           VARCHAR(100),
    step_type           VARCHAR(50) NOT NULL,          -- 'approval', 'notification', 'action', 'wait', 'branch'
    approver_type       VARCHAR(50),                   -- 'supervisor', 'role', 'specific_user', 'expression'
    approver_value      VARCHAR(200),                  -- Role name, user ID, or expression
    timeout_hours       INTEGER,
    timeout_action      VARCHAR(50),                   -- 'escalate', 'auto_approve', 'auto_reject'
    conditions          JSONB,                         -- When to execute this step
    actions_on_approve  JSONB,
    actions_on_reject   JSONB,
    next_step_approve   UUID,
    next_step_reject    UUID,
    UNIQUE(workflow_id, step_seq)
);

-- ============================================================
-- JURISDICTION HIERARCHY: Federal > State > Local
-- ============================================================
CREATE TABLE bl_jurisdictions (
    jurisdiction_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_code   VARCHAR(50) UNIQUE NOT NULL,   -- 'US', 'US-CA', 'US-CA-SF'
    jurisdiction_name   VARCHAR(200),
    parent_jurisdiction VARCHAR(50),                   -- Parent code
    jurisdiction_level  INTEGER,                       -- 1=Federal, 2=State, 3=Local
    country_code        VARCHAR(3),
    state_code          VARCHAR(10),
    locality_code       VARCHAR(50),
    effective_date      DATE,
    is_active           BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- RULE CHANGE HISTORY: Full audit trail
-- ============================================================
CREATE TABLE bl_rule_changes (
    change_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID NOT NULL,
    change_type         VARCHAR(20) NOT NULL,          -- 'CREATE', 'UPDATE', 'DELETE', 'ACTIVATE', 'DEACTIVATE'
    changed_at          TIMESTAMP DEFAULT NOW(),
    changed_by          VARCHAR(100),
    change_reason       TEXT,
    source_document     VARCHAR(500),
    previous_state      JSONB,                         -- Full rule state before change
    new_state           JSONB,                         -- Full rule state after change
    approved_by         VARCHAR(100),
    approved_at         TIMESTAMP
);

-- ============================================================
-- RULE EXECUTION LOG: Runtime audit
-- ============================================================
CREATE TABLE bl_rule_executions (
    execution_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id      UUID NOT NULL,                 -- Groups related rule executions
    rule_id             UUID NOT NULL,
    executed_at         TIMESTAMP DEFAULT NOW(),
    executed_by         VARCHAR(100),                  -- User or system
    entity_type         VARCHAR(100),
    entity_key          JSONB,                         -- {"EMPLID": "12345", "EMPL_RCD": 0}
    conditions_evaluated JSONB,                        -- What was checked
    condition_results   JSONB,                         -- True/False for each
    rule_matched        BOOLEAN,                       -- Did conditions pass?
    actions_executed    JSONB,                         -- What actions ran
    action_results      JSONB,                         -- Results of actions
    errors              JSONB,
    warnings            JSONB,
    execution_time_ms   INTEGER
);

-- Indexes for performance
CREATE INDEX idx_rules_entity ON bl_rules(entity_id);
CREATE INDEX idx_rules_trigger ON bl_rules(trigger_event);
CREATE INDEX idx_rules_category ON bl_rules(category);
CREATE INDEX idx_rules_jurisdiction ON bl_rules(jurisdiction);
CREATE INDEX idx_rules_effective ON bl_rules(effective_date, expiration_date);
CREATE INDEX idx_rule_conditions_rule ON bl_rule_conditions(rule_id);
CREATE INDEX idx_rule_actions_rule ON bl_rule_actions(rule_id);
CREATE INDEX idx_executions_transaction ON bl_rule_executions(transaction_id);
CREATE INDEX idx_executions_rule ON bl_rule_executions(rule_id);
CREATE INDEX idx_executions_time ON bl_rule_executions(executed_at);
```

---

## Rule Extraction from PeopleSoft

### Extraction Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACTION PIPELINE                           │
│                                                                  │
│  ┌──────────────┐                                               │
│  │  PeopleSoft  │                                               │
│  │   Database   │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Record     │────▶│  PeopleCode  │────▶│   Workflow   │    │
│  │  Metadata    │     │   Extractor  │     │  Extractor   │    │
│  │  Extractor   │     │              │     │              │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM Translator                        │   │
│  │                                                          │   │
│  │  • Parses PeopleCode syntax                             │   │
│  │  • Identifies conditions, actions, loops                │   │
│  │  • Translates to rule JSON format                       │   │
│  │  • Preserves source location for traceability           │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌──────────────┐                         │
│  │    Human     │────▶│     Rule     │                         │
│  │    Review    │     │   Database   │                         │
│  └──────────────┘     └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### MCP Tools for Extraction

```python
# New tools to add to peoplesoft-mcp for rule extraction

@tool
async def extract_record_rules(record_name: str) -> dict:
    """
    Extract all business rules from a PeopleSoft record.
    
    Returns:
        - Record metadata (fields, keys, effective dating)
        - PeopleCode events and their logic
        - Field-level validations (XLAT, required, etc.)
        - Derived field calculations
    """

@tool
async def extract_peoplecode_as_rules(
    record_name: str, 
    field_name: str = None,
    event: str = None
) -> list[dict]:
    """
    Parse PeopleCode and convert to declarative rule format.
    
    Returns list of rules with:
        - conditions (IF statements)
        - actions (assignments, errors, function calls)
        - loops (converted to batch rules)
        - source location for traceability
    """

@tool
async def extract_component_rules(component_name: str) -> dict:
    """
    Extract all rules associated with a component.
    
    Returns:
        - Component-level PeopleCode (SearchInit, PostBuild, etc.)
        - All record PeopleCode used in the component
        - Page-level field defaults and validations
        - Security rules (who can access)
    """

@tool
async def extract_application_engine_rules(ae_program: str) -> dict:
    """
    Extract rules from Application Engine programs.
    
    Returns:
        - Program structure (sections, steps)
        - SQL actions and their logic
        - PeopleCode actions
        - Conditional execution (Do When, Do While)
    """

@tool
async def extract_workflow_rules(workflow_name: str) -> dict:
    """
    Extract approval workflow definitions.
    
    Returns:
        - Trigger events
        - Routing rules (who approves)
        - Step sequence
        - Notifications
    """

@tool  
async def analyze_peoplecode_complexity(record_name: str) -> dict:
    """
    Analyze PeopleCode to estimate extraction difficulty.
    
    Returns:
        - Lines of code
        - Complexity score (cyclomatic)
        - External function calls
        - SQL statements
        - Recommendation: simple_rule | complex_rule | needs_code
    """
```

### Example: PeopleCode to Rule Conversion

**Original PeopleCode:**

```peoplecode
/* Record: JOB, Field: DEPTID, Event: FieldChange */

Local string &supervisor;

If %Mode = "A" Or %Mode = "U" Then
   If EFFDT <= %Date Then
      
      /* Get supervisor from department */
      SQLExec("SELECT MANAGER_ID FROM PS_DEPT_TBL WHERE SETID = :1 AND DEPTID = :2 AND EFFDT = (SELECT MAX(EFFDT) FROM PS_DEPT_TBL WHERE SETID = :1 AND DEPTID = :2 AND EFFDT <= %DateIn(:3))", 
              SETID_DEPT, DEPTID, %Date, &supervisor);
      
      If All(&supervisor) Then
         SUPERVISOR_ID = &supervisor;
         REPORTS_TO = &supervisor;
      Else
         If All(SUPERVISOR_ID) Then
            REPORTS_TO = SUPERVISOR_ID;
         Else
            If HR_STATUS = "A" Then
               Error MsgGet(1000, 100, "Active employees must have a supervisor");
            End-If;
         End-If;
      End-If;
      
   End-If;
End-If;
```

**Extracted Rules:**

```json
[
  {
    "rule_id": "JOB-DEPTID-001",
    "rule_name": "Auto-populate Supervisor from Department",
    "rule_type": "default",
    "entity": "Job",
    "trigger_event": "on_change:DEPTID",
    "source_system": "PeopleSoft:JOB.DEPTID.FieldChange",
    "priority": 10,
    "conditions": [
      {"attribute": "mode", "operator": "in_list", "value": ["A", "U"]},
      {"attribute": "job.effdt", "operator": "less_than_or_equal", "value": {"function": "current_date"}}
    ],
    "actions": [
      {
        "action_type": "lookup",
        "lookup_entity": "Department",
        "lookup_key": {"setid": "job.setid_dept", "deptid": "job.deptid"},
        "lookup_field": "manager_id",
        "target": "job.supervisor_id",
        "condition": {"result": "is_not_null"}
      },
      {
        "action_type": "set_value",
        "target": "job.reports_to",
        "value": {"ref": "job.supervisor_id"},
        "condition": {"attribute": "job.supervisor_id", "operator": "is_not_null"}
      }
    ]
  },
  {
    "rule_id": "JOB-DEPTID-002",
    "rule_name": "Supervisor Required for Active Employees",
    "rule_type": "validation",
    "entity": "Job",
    "trigger_event": "on_change:DEPTID",
    "source_system": "PeopleSoft:JOB.DEPTID.FieldChange",
    "priority": 20,
    "conditions": [
      {"attribute": "mode", "operator": "in_list", "value": ["A", "U"]},
      {"attribute": "job.effdt", "operator": "less_than_or_equal", "value": {"function": "current_date"}},
      {"attribute": "job.supervisor_id", "operator": "is_null"},
      {"attribute": "job.hr_status", "operator": "equals", "value": "A"}
    ],
    "actions": [
      {
        "action_type": "error",
        "error_code": "1000-100",
        "error_message": "Active employees must have a supervisor"
      }
    ]
  }
]
```

---

## Agent Architecture

### Agent Types

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT ECOSYSTEM                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               TRANSACTION AGENT (Primary)                │   │
│  │                                                          │   │
│  │  Handles all HR transactions:                           │   │
│  │  • Hire, Transfer, Promote, Terminate                   │   │
│  │  • Job data changes                                     │   │
│  │  • Benefits enrollment                                  │   │
│  │  • Leave requests                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               COMPLIANCE AGENT                           │   │
│  │                                                          │   │
│  │  Monitors and updates rules:                            │   │
│  │  • Reads regulatory publications                        │   │
│  │  • Proposes rule updates                                │   │
│  │  • Calculates impact                                    │   │
│  │  • Tracks compliance deadlines                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               PAYROLL AGENT                              │   │
│  │                                                          │   │
│  │  Processes payroll calculations:                        │   │
│  │  • Determines applicable tax rules                      │   │
│  │  • Calculates gross-to-net                              │   │
│  │  • Handles retro adjustments                            │   │
│  │  • Orchestrates Rust calculation engine                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               REPORTING AGENT                            │   │
│  │                                                          │   │
│  │  Generates regulatory reports:                          │   │
│  │  • W-2, 1099, ACA 1095-C                               │   │
│  │  • EEO-1, VETS-4212                                     │   │
│  │  • State/local reporting                                │   │
│  │  • Explains data sources and calculations               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               EXTRACTION AGENT                           │   │
│  │                                                          │   │
│  │  Migrates from PeopleSoft:                              │   │
│  │  • Reads PeopleCode                                     │   │
│  │  • Translates to rule format                            │   │
│  │  • Validates extracted rules                            │   │
│  │  • Identifies gaps                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Tools

```python
# ============================================================
# DATA ACCESS TOOLS
# ============================================================

@tool
async def query_entity(
    entity: str,
    filters: dict = None,
    include_history: bool = False,
    as_of_date: str = None
) -> list[dict]:
    """
    Query operational data with automatic effective dating.
    
    Args:
        entity: Entity name ('Employee', 'Job', 'Department')
        filters: Field filters {"emplid": "12345", "hr_status": "A"}
        include_history: If True, return all effective-dated rows
        as_of_date: Point-in-time query (default: today)
    
    Returns:
        List of entity records
    """

@tool
async def save_entity(
    entity: str,
    data: dict,
    mode: str = "update"  # 'insert', 'update', 'correct', 'delete'
) -> dict:
    """
    Persist entity changes with rule validation.
    
    The save operation:
    1. Loads applicable rules for the entity
    2. Evaluates pre-save validations
    3. Applies defaults and calculations
    4. If no errors, persists to database
    5. Executes post-save actions (workflows, notifications)
    6. Returns result with any warnings
    """

@tool
async def get_related_entities(
    entity: str,
    entity_key: dict,
    relationship: str
) -> list[dict]:
    """
    Navigate entity relationships.
    
    Examples:
        get_related_entities('Employee', {'emplid': '12345'}, 'jobs')
        get_related_entities('Job', {'emplid': '12345', 'empl_rcd': 0}, 'department')
    """

# ============================================================
# RULE ENGINE TOOLS
# ============================================================

@tool
async def get_applicable_rules(
    entity: str,
    event: str,
    context: dict = None
) -> list[dict]:
    """
    Retrieve rules that apply to an entity/event.
    
    Args:
        entity: Entity name
        event: Trigger event ('on_save', 'on_change:DEPTID', etc.)
        context: Additional context for jurisdiction filtering
    
    Returns:
        Rules sorted by priority, filtered by:
        - Active status
        - Effective date
        - Jurisdiction applicability
    """

@tool
async def evaluate_condition(
    condition: dict,
    context: dict
) -> dict:
    """
    Evaluate a single rule condition.
    
    Returns:
        {
            "result": True/False,
            "attribute_value": <actual value>,
            "comparison_value": <expected value>,
            "explanation": "employee.hr_status ('A') equals 'A'"
        }
    """

@tool
async def evaluate_expression(
    expression_id: str,
    parameters: dict
) -> dict:
    """
    Evaluate a calculation expression.
    
    Returns:
        {
            "result": <calculated value>,
            "expression": "base_salary * 1.03",
            "inputs": {"base_salary": 50000},
            "explanation": "50000 * 1.03 = 51500"
        }
    """

@tool
async def execute_action(
    action: dict,
    context: dict
) -> dict:
    """
    Execute a rule action.
    
    Handles action types:
    - set_value: Update a field
    - error/warning: Add to result messages
    - create_record: Insert related entity
    - call_service: Invoke external API
    - start_workflow: Initiate approval process
    
    Returns:
        {
            "success": True/False,
            "action_type": "set_value",
            "target": "job.reports_to",
            "old_value": null,
            "new_value": "MGR001",
            "explanation": "Set reports_to to supervisor_id value"
        }
    """

@tool
async def lookup_rate_table(
    table_code: str,
    lookup_value: float,
    context: dict = None
) -> dict:
    """
    Look up value in a rate table (tax brackets, etc.).
    
    Args:
        table_code: Rate table identifier ('FED-WITHHOLD-2026-SINGLE')
        lookup_value: Value to look up (e.g., taxable wages)
        context: Filing status, jurisdiction, etc.
    
    Returns:
        {
            "bracket_rate": 0.22,
            "bracket_floor": 48476,
            "bracket_ceiling": 103350,
            "base_tax": 5426,
            "calculation": "5426 + (wages - 48475) * 0.22"
        }
    """

# ============================================================
# JURISDICTION TOOLS
# ============================================================

@tool
async def get_applicable_jurisdictions(
    employee_context: dict
) -> list[str]:
    """
    Determine which jurisdictions apply to an employee.
    
    Based on:
    - Work location
    - Resident location
    - Company registration
    
    Returns ordered list: ['US', 'US-CA', 'US-CA-SF']
    """

@tool
async def resolve_jurisdiction_conflict(
    rules: list[dict],
    jurisdictions: list[str]
) -> dict:
    """
    Resolve conflicting rules across jurisdictions.
    
    Resolution order:
    1. Most specific jurisdiction wins (local > state > federal)
    2. Most generous to employee (for leave, benefits)
    3. Most restrictive (for compliance)
    
    Returns the winning rule with explanation.
    """

# ============================================================
# AUDIT TOOLS
# ============================================================

@tool
async def log_rule_execution(
    transaction_id: str,
    rule_id: str,
    context: dict,
    conditions_evaluated: list,
    actions_executed: list,
    result: dict
) -> None:
    """
    Write detailed audit log of rule execution.
    """

@tool
async def explain_decision(
    transaction_id: str
) -> str:
    """
    Generate human-readable explanation of all rules
    that fired for a transaction.
    
    Returns markdown explanation citing rules and their sources.
    """

# ============================================================
# WORKFLOW TOOLS
# ============================================================

@tool
async def start_workflow(
    workflow_code: str,
    entity: str,
    entity_key: dict,
    initiator: str
) -> dict:
    """
    Initiate an approval workflow.
    """

@tool
async def get_pending_approvals(
    approver: str
) -> list[dict]:
    """
    Get items pending approval for a user.
    """

@tool
async def submit_approval_decision(
    workflow_instance_id: str,
    decision: str,  # 'approve', 'reject', 'return'
    comments: str = None
) -> dict:
    """
    Record approval decision and advance workflow.
    """
```

### Agent Skills

```markdown
# ============================================================
# SKILL: HR Domain Expert
# ============================================================

You are an HR domain expert. You understand:

## Effective Dating
- Most HR data is effective-dated (EFFDT)
- To get current data: MAX(EFFDT) WHERE EFFDT <= CURRENT_DATE
- Future-dated rows represent scheduled changes
- EFFSEQ handles multiple changes on the same date

## Employee Records
- EMPLID: Unique person identifier
- EMPL_RCD: Employment record number (0, 1, 2...)
- A person can have multiple EMPL_RCDs (concurrent jobs)
- Each EMPL_RCD has its own job history

## Action Codes
- HIR = Hire
- REH = Rehire
- TER = Termination
- XFR = Transfer
- PRO = Promotion
- DEM = Demotion
- LOA = Leave of Absence
- RFL = Return from Leave
- PAY = Pay Rate Change

## Status Codes
- HR_STATUS: A=Active, I=Inactive
- EMPL_STATUS: A=Active, L=Leave, P=Paid Leave, T=Terminated, D=Deceased, R=Retired

When processing transactions, always:
1. Verify effective date is valid
2. Check for existing future-dated rows that might conflict
3. Ensure proper action/reason code combination
4. Validate status transitions are allowed


# ============================================================
# SKILL: Tax Calculation Expert
# ============================================================

You are a payroll tax expert. You understand:

## Federal Taxes
- Federal Income Tax (FIT): Progressive brackets, W-4 based
- Social Security (OASDI): 6.2% up to wage base ($176,100 in 2026)
- Medicare: 1.45% (no limit), +0.9% Additional Medicare over $200k
- FUTA: 6.0% (0.6% after credit) on first $7,000

## State Taxes
- State Income Tax: Varies by state (some states have none)
- State Disability (SDI): CA, NJ, NY, etc.
- State Unemployment (SUI): Employer paid, varies by experience rating
- Local taxes: City, county, school district

## Withholding Order
1. Calculate gross pay
2. Subtract pre-tax deductions (401k, FSA, etc.)
3. Calculate taxable wages per tax type
4. Apply federal withholding (Publication 15-T method)
5. Apply state withholding
6. Apply local withholding
7. Subtract post-tax deductions

## Multi-State Rules
- Resident state: Usually withholds
- Work state: May require withholding (reciprocity agreements)
- Some states have "convenience of employer" rules


# ============================================================
# SKILL: Compliance Expert
# ============================================================

You are a regulatory compliance expert. You understand:

## Key Regulations
- FLSA: Overtime, minimum wage, exempt/non-exempt
- FMLA: Family medical leave (50+ employees)
- ACA: Health coverage requirements (50+ FTEs)
- ERISA: Retirement plan requirements
- COBRA: Continuation coverage
- HIPAA: Health data privacy

## Reporting Requirements
- W-2: Annual wage/tax statement (due Jan 31)
- 1095-C: ACA coverage reporting (due March 2)
- EEO-1: Workforce demographics (due varies)
- VETS-4212: Veteran employment (due Sept 30)
- Multiple Worksite Report: BLS quarterly

## State-Specific
- CA: Extensive leave laws, pay transparency, CCPA
- NY: Paid family leave, wage theft prevention
- Other states: Varying requirements

When monitoring compliance:
1. Track regulatory calendar deadlines
2. Monitor for rule changes from official sources
3. Assess impact on existing rules
4. Propose updates with citations
```

### Agent Rules (Guardrails)

```markdown
# ============================================================
# RULE: Always Audit
# ============================================================

Before ANY data modification:
1. Record transaction_id (UUID for this operation)
2. Record before-state of affected records
3. Record user identity and timestamp

After successful save:
4. Record after-state
5. Record all rules that fired
6. Record explanation of changes

This audit trail is NON-NEGOTIABLE. Even system operations must be logged.


# ============================================================
# RULE: Never Auto-Apply Regulatory Changes
# ============================================================

When the Compliance Agent identifies a regulatory change:

1. CREATE a change proposal (not apply directly)
2. CALCULATE impact (affected employees, estimated change)
3. NOTIFY compliance team
4. WAIT for human approval
5. Only THEN apply the rule change

EXCEPTION: None. All regulatory changes require human review.


# ============================================================
# RULE: Validate Before Save
# ============================================================

Before any save_entity call:

1. Load ALL applicable rules for the entity and event
2. Evaluate ALL validation rules (rule_type = 'validation')
3. COLLECT all errors and warnings
4. If ANY errors exist, REJECT the save
5. Return ALL errors (not just the first one)

Do not short-circuit validation - users need complete feedback.


# ============================================================
# RULE: Respect Effective Dating
# ============================================================

For effective-dated entities:

1. EFFDT is REQUIRED
2. Cannot create rows with EFFDT > CURRENT_DATE + 365 without approval
3. Cannot modify rows with EFFDT < CURRENT_DATE - 365 without approval
4. Corrections to historical data require audit justification
5. Future-dated changes must not conflict with existing future rows


# ============================================================
# RULE: Security First
# ============================================================

Before returning ANY data:

1. Verify user has access to the entity type
2. Apply row-level security (department, company, etc.)
3. Mask sensitive fields based on role:
   - SSN: Show only last 4 unless Payroll role
   - Salary: Hide unless Manager of employee or Compensation role
   - Medical: Never display in standard queries
4. Log all data access for audit


# ============================================================
# RULE: Explain Everything
# ============================================================

For EVERY transaction result, provide:

1. List of rules that were evaluated
2. Which rules fired (conditions met)
3. What actions were taken
4. Source citations for key rules
5. Natural language summary

Users should NEVER wonder "why did the system do that?"
```

---

## Regulatory Compliance Agent

### Overview

The Compliance Agent continuously monitors regulatory sources and proposes rule updates.

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE AGENT WORKFLOW                     │
│                                                                  │
│  ┌──────────────┐                                               │
│  │  Regulatory  │  IRS, DOL, SSA, State agencies                │
│  │   Sources    │  News feeds, official publications            │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼ (scheduled scan)                                       │
│  ┌──────────────┐                                               │
│  │    Parse     │  Extract structured data from                 │
│  │  Documents   │  PDFs, web pages, press releases              │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   Identify   │  Match changes to existing rules              │
│  │   Affected   │  Find rules by category, jurisdiction         │
│  │    Rules     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   Generate   │  Create rule change proposals                 │
│  │   Proposal   │  with before/after diff                       │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  Calculate   │  Affected employees, financial impact         │
│  │   Impact     │  First affected payroll date                  │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌──────────────┐                         │
│  │   Submit     │────▶│    Human     │                         │
│  │ for Review   │     │   Approval   │                         │
│  └──────────────┘     └──────┬───────┘                         │
│                              │                                   │
│                              ▼ (approved)                        │
│                       ┌──────────────┐                          │
│                       │    Apply     │                          │
│                       │    Rules     │                          │
│                       └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### Compliance Agent Tools

```python
@tool
async def fetch_regulatory_document(
    source: str,
    document_id: str = None,
    url: str = None
) -> dict:
    """
    Fetch and parse a regulatory document.
    
    Sources: 'IRS', 'DOL', 'SSA', 'CA-EDD', etc.
    
    Returns:
        {
            "title": "Revenue Procedure 2025-XX",
            "publication_date": "2025-11-15",
            "effective_date": "2026-01-01",
            "content": "<parsed content>",
            "tables": [<extracted tables>],
            "key_changes": [<identified changes>]
        }
    """

@tool
async def find_affected_rules(
    change_category: str,
    jurisdiction: str = None,
    keywords: list[str] = None
) -> list[dict]:
    """
    Find existing rules affected by a regulatory change.
    
    Args:
        change_category: 'tax_brackets', 'minimum_wage', 'leave', etc.
        jurisdiction: 'US', 'US-CA', etc.
        keywords: Additional search terms
    
    Returns:
        List of rules that may need updating
    """

@tool
async def create_rule_change_proposal(
    affected_rule_id: str,
    changes: list[dict],
    source_document: str,
    effective_date: str
) -> dict:
    """
    Create a formal rule change proposal.
    
    Args:
        affected_rule_id: Rule to modify (or 'NEW' for new rule)
        changes: List of field changes with old/new values
        source_document: Citation for the regulatory source
        effective_date: When the change takes effect
    
    Returns:
        Proposal object with diff view
    """

@tool
async def calculate_change_impact(
    proposal_id: str
) -> dict:
    """
    Calculate the impact of a proposed rule change.
    
    Returns:
        {
            "affected_employees": 12543,
            "affected_payrolls": ["2026-01-15", "2026-01-31"],
            "estimated_financial_impact": {
                "per_employee_avg": -45.00,
                "total_annual": -564435.00
            },
            "jurisdictions_affected": ["US"],
            "risk_assessment": "LOW"
        }
    """

@tool
async def submit_for_approval(
    proposal_id: str,
    urgency: str = "normal",  # 'normal', 'urgent', 'critical'
    notes: str = None
) -> dict:
    """
    Submit rule change proposal for human approval.
    
    Creates workflow item for compliance team review.
    """

@tool
async def get_compliance_calendar() -> list[dict]:
    """
    Get upcoming regulatory deadlines.
    
    Returns:
        [
            {
                "deadline": "2026-01-31",
                "requirement": "W-2 Distribution",
                "description": "Furnish W-2 to employees",
                "penalty": "$50/statement up to $580,000"
            },
            ...
        ]
    """

@tool
async def scan_for_updates(
    sources: list[str] = None,
    since_date: str = None
) -> list[dict]:
    """
    Scan regulatory sources for new publications.
    
    Returns list of new/updated documents since last scan.
    """
```

### Example: Tax Bracket Update Flow

```
Agent receives scheduled trigger: "Scan IRS for 2026 updates"

1. scan_for_updates(sources=['IRS'], since_date='2025-10-01')
   → Found: "Revenue Procedure 2025-45" (inflation adjustments)

2. fetch_regulatory_document(source='IRS', document_id='Rev-Proc-2025-45')
   → Parsed document with tax tables

3. Agent analyzes extracted tables:
   "I found updated tax brackets for 2026. Comparing to current rules..."

4. find_affected_rules(change_category='tax_brackets', jurisdiction='US')
   → Returns: ['FED-WITHHOLD-2025-SINGLE', 'FED-WITHHOLD-2025-MFJ', ...]

5. For each affected rule:
   create_rule_change_proposal(
       affected_rule_id='FED-WITHHOLD-2025-SINGLE',
       changes=[
           {"path": "table_rows[0].upper_bound", "old": 11600, "new": 11925},
           {"path": "table_rows[1].lower_bound", "old": 11601, "new": 11926},
           ...
       ],
       source_document='IRS Rev. Proc. 2025-45, Table 1',
       effective_date='2026-01-01'
   )

6. calculate_change_impact(proposal_id='...')
   → "12,543 employees affected, avg $45/year tax reduction"

7. submit_for_approval(proposal_id='...', urgency='normal')
   → Creates task for compliance team

8. Agent summarizes:
   "I've created 4 rule change proposals for the 2026 federal tax updates:
    - Single filer brackets: 7 rows updated
    - MFJ brackets: 7 rows updated
    - Standard deduction: Updated for all filing statuses
    - 401(k) limit: Increased to $24,000
    
    Total impact: 12,543 employees, ~$564K annual tax savings
    First affected payroll: 2026-01-15
    
    Proposals submitted for review. Deadline: 2025-12-15 for January payroll."
```

---

## Multi-Jurisdiction Handling

### Jurisdiction Hierarchy

```
                         ┌─────────────┐
                         │   FEDERAL   │
                         │    (US)     │
                         └──────┬──────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
  ┌───────────┐          ┌───────────┐          ┌───────────┐
  │   STATE   │          │   STATE   │          │   STATE   │
  │   (CA)    │          │   (NY)    │          │   (TX)    │
  └─────┬─────┘          └─────┬─────┘          └───────────┘
        │                      │                 (no state tax)
   ┌────┴────┐            ┌────┴────┐
   ▼         ▼            ▼         ▼
┌─────┐  ┌─────┐      ┌─────┐  ┌─────┐
│ SF  │  │ LA  │      │ NYC │  │Yonk-│
│     │  │     │      │     │  │ers  │
└─────┘  └─────┘      └─────┘  └─────┘
```

### Rule Precedence

```python
# Jurisdiction precedence rules

PRECEDENCE_RULES = {
    "tax": {
        # All jurisdictions apply (stacking)
        "method": "stack",
        "order": ["federal", "state", "local"]
    },
    "minimum_wage": {
        # Highest rate wins
        "method": "max",
        "order": ["local", "state", "federal"]
    },
    "leave": {
        # Most generous wins (usually)
        "method": "max_benefit",
        "order": ["local", "state", "federal"]
    },
    "overtime": {
        # Most restrictive wins (to protect employee)
        "method": "most_restrictive", 
        "order": ["local", "state", "federal"]
    }
}
```

### Multi-Jurisdiction Example

```
Employee works in San Francisco, lives in Oakland

Applicable jurisdictions (determined by get_applicable_jurisdictions):
- Federal: US
- State: US-CA (work and residence)
- Local: US-CA-SF (work location)

Minimum Wage Resolution:
1. Federal minimum: $7.25/hr
2. CA minimum: $16.50/hr
3. SF minimum: $18.67/hr
→ Winner: SF at $18.67/hr (highest)

Tax Withholding (stacking):
1. Federal income tax: Calculate per Publication 15-T
2. CA state income tax: Calculate per CA PIT tables
3. CA SDI: 1.1% of wages up to $173,243
4. SF Paid Parental Leave: 0.1% of wages
→ All apply (deduct all)

Overtime Rules:
1. Federal (FLSA): OT after 40 hrs/week
2. CA: OT after 8 hrs/day AND after 40 hrs/week
→ Winner: CA (more restrictive = more OT pay for employee)

Agent explanation:
"For employee 12345 working in San Francisco:
 - Minimum wage: $18.67/hr (SF Minimum Wage Ordinance)
 - Overtime: CA daily overtime rules apply (CA Labor Code 510)
 - Taxes: Federal + CA State + CA SDI + SF PPLO
 
 Sources:
 - SF Min Wage: SF Admin Code Chapter 12R
 - CA Overtime: Labor Code Section 510
 - CA SDI: UI Code Section 984"
```

---

## Execution Flow

### Transaction Processing

```
┌─────────────────────────────────────────────────────────────────┐
│              TRANSACTION EXECUTION SEQUENCE                      │
│                                                                  │
│  INPUT: User submits job change (transfer to new department)    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1. LOAD CONTEXT                                             ││
│  │    • Get current employee data                              ││
│  │    • Get current job record                                 ││
│  │    • Identify changed fields: [DEPTID]                      ││
│  │    • Determine jurisdictions                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 2. LOAD RULES                                               ││
│  │    • get_applicable_rules('Job', 'on_change:DEPTID')        ││
│  │    • Filter by jurisdiction, effective date                 ││
│  │    • Sort by priority                                       ││
│  │    → Returns 5 rules                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 3. EVALUATE CONDITIONS (for each rule)                      ││
│  │                                                             ││
│  │    Rule 1: "Auto-set Supervisor"                            ││
│  │    • Condition: mode IN ('A','U') → TRUE                    ││
│  │    • Condition: EFFDT <= today → TRUE                       ││
│  │    → Rule MATCHES                                           ││
│  │                                                             ││
│  │    Rule 2: "Supervisor Required"                            ││
│  │    • Condition: HR_STATUS = 'A' → TRUE                      ││
│  │    • Condition: SUPERVISOR_ID IS NULL → FALSE               ││
│  │    → Rule does NOT match                                    ││
│  │                                                             ││
│  │    ... evaluate remaining rules ...                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 4. EXECUTE ACTIONS (for matching rules)                     ││
│  │                                                             ││
│  │    Rule 1 actions:                                          ││
│  │    • Lookup department manager → MGR001                     ││
│  │    • Set SUPERVISOR_ID = MGR001                             ││
│  │    • Set REPORTS_TO = MGR001                                ││
│  │                                                             ││
│  │    Rule 3 actions:                                          ││
│  │    • Queue notification: "Notify old manager"               ││
│  │                                                             ││
│  │    Rule 4 actions:                                          ││
│  │    • Queue background job: "Update org chart cache"         ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 5. VALIDATION CHECK                                         ││
│  │    • Collect all errors from rules → 0 errors               ││
│  │    • Collect all warnings → 1 warning                       ││
│  │    → VALIDATION PASSED                                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 6. PERSIST CHANGES                                          ││
│  │    • Begin transaction                                      ││
│  │    • Insert new JOB row                                     ││
│  │    • Write audit log                                        ││
│  │    • Commit transaction                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 7. POST-SAVE PROCESSING                                     ││
│  │    • Execute queued notifications                           ││
│  │    • Trigger background jobs                                ││
│  │    • Start workflows if needed                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 8. RETURN RESULT                                            ││
│  │                                                             ││
│  │  {                                                          ││
│  │    "success": true,                                         ││
│  │    "entity": "Job",                                         ││
│  │    "key": {"emplid": "12345", "empl_rcd": 0, "effdt": ...},││
│  │    "changes": [                                             ││
│  │      {"field": "DEPTID", "old": "10100", "new": "10200"},  ││
│  │      {"field": "SUPERVISOR_ID", "old": null, "new": "MGR1"}││
│  │    ],                                                       ││
│  │    "warnings": ["Old manager will be notified"],            ││
│  │    "rules_fired": ["JOB-DEPTID-001", "JOB-DEPTID-003"],    ││
│  │    "explanation": "Department changed to 10200. Supervisor ││
│  │      automatically set to department manager (Rule          ││
│  │      JOB-DEPTID-001). Notification sent to previous        ││
│  │      manager (Rule JOB-DEPTID-003)."                        ││
│  │  }                                                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### When to Use Agents vs. Compiled Code

| Scenario | Use Agent | Use Compiled Code |
|----------|-----------|-------------------|
| Complex rule selection | ✓ | |
| Simple validation | | ✓ (rule engine) |
| Tax calculation | Agent selects rules | Rust calculates |
| Batch payroll (10K+ employees) | | ✓ (with cached rules) |
| Ad-hoc queries | ✓ | |
| Real-time UI validation | | ✓ (cached simple rules) |

### Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PERFORMANCE TIERS                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TIER 1: Agent (LLM-based)                                   ││
│  │ • Complex rule selection                                    ││
│  │ • Jurisdiction resolution                                   ││
│  │ • Explanation generation                                    ││
│  │ • Novel situations                                          ││
│  │                                                             ││
│  │ Latency: 500ms - 2s                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TIER 2: Rule Engine (Deterministic)                         ││
│  │ • Simple condition evaluation                               ││
│  │ • Cached rule execution                                     ││
│  │ • Standard validations                                      ││
│  │                                                             ││
│  │ Latency: 10ms - 50ms                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TIER 3: Compiled (Rust/Go)                                  ││
│  │ • Payroll calculation engine                                ││
│  │ • Tax bracket lookups                                       ││
│  │ • Batch processing                                          ││
│  │                                                             ││
│  │ Latency: <1ms per calculation                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Caching Strategy

```python
CACHE_CONFIG = {
    "rules": {
        "ttl": 300,  # 5 minutes
        "invalidate_on": ["rule_change", "jurisdiction_change"]
    },
    "rate_tables": {
        "ttl": 86400,  # 24 hours (changes are infrequent)
        "invalidate_on": ["rate_table_change"]
    },
    "jurisdictions": {
        "ttl": 3600,  # 1 hour
        "invalidate_on": ["jurisdiction_change"]
    },
    "employee_context": {
        "ttl": 60,  # 1 minute
        "scope": "transaction"  # Cache per transaction
    }
}
```

---

## Security Model

### Access Control

```sql
-- Row-level security rules
CREATE TABLE bl_security_rules (
    security_rule_id    UUID PRIMARY KEY,
    entity_id           UUID REFERENCES bl_entities,
    role                VARCHAR(100),
    access_type         VARCHAR(20),  -- 'read', 'write', 'admin'
    filter_expression   JSONB         -- Row filter
);

-- Example: HR can only see their department
INSERT INTO bl_security_rules VALUES (
    gen_random_uuid(),
    (SELECT entity_id FROM bl_entities WHERE entity_name = 'Employee'),
    'HR_GENERALIST',
    'read',
    '{"department": {"ref": "user.department"}}'
);
```

### Field-Level Masking

```python
FIELD_MASKING = {
    "ssn": {
        "default": "***-**-{last4}",
        "roles_full_access": ["PAYROLL_ADMIN", "SECURITY_ADMIN"]
    },
    "salary": {
        "default": "HIDDEN",
        "roles_full_access": ["COMPENSATION", "MANAGER_OF_EMPLOYEE"]
    },
    "bank_account": {
        "default": "****{last4}",
        "roles_full_access": ["PAYROLL_ADMIN"]
    }
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

- [ ] Set up PostgreSQL with rule schema
- [ ] Build basic CRUD API for rule management
- [ ] Implement rule engine (deterministic evaluation)
- [ ] Create first agent tools (query_entity, get_applicable_rules)

### Phase 2: Extraction (Months 2-3)

- [ ] Enhance peoplesoft-mcp with extraction tools
- [ ] Build PeopleCode parser
- [ ] Extract rules from one pilot component (e.g., Job)
- [ ] Validate extracted rules against PeopleSoft behavior

### Phase 3: Agent Integration (Months 3-4)

- [ ] Implement Transaction Agent
- [ ] Build all agent tools
- [ ] Create agent skills (HR domain, effective dating)
- [ ] Implement agent rules (audit, security)

### Phase 4: Compliance Agent (Month 4-5)

- [ ] Build regulatory source integrations
- [ ] Implement change proposal workflow
- [ ] Create impact analysis tools
- [ ] Test with real regulatory updates

### Phase 5: Payroll Engine (Months 5-7)

- [ ] Build Rust calculation engine
- [ ] Integrate with agent for rule selection
- [ ] Extract payroll rules from GP
- [ ] Parallel testing with PeopleSoft

### Phase 6: Full Migration (Months 7-12)

- [ ] Extract remaining modules
- [ ] Build web UI
- [ ] User acceptance testing
- [ ] Cutover planning

---

## Technology Stack

### Recommended Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| **Rule Database** | PostgreSQL | JSONB support, excellent for structured rules |
| **API Layer** | Python + FastAPI | Fast development, good for agent integration |
| **Agent Runtime** | Claude/GPT-4 | Best reasoning capabilities |
| **Calculation Engine** | Rust | Performance for payroll/tax |
| **Batch Processing** | Go | Concurrent processing, simple deployment |
| **Frontend** | React + TypeScript | Large ecosystem, good typing |
| **Caching** | Redis | Rule caching, session state |
| **Search** | Elasticsearch | Full-text search on rules |
| **Monitoring** | OpenTelemetry + Grafana | Observability |

### File Structure

```
hr-agent-system/
├── rule-database/
│   ├── migrations/           # SQL schema migrations
│   └── seed/                 # Initial rule data
├── api/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # FastAPI routes
│   │   ├── services/        # Business logic
│   │   └── agents/          # Agent implementations
│   └── tests/
├── rule-engine/              # Deterministic rule evaluation
│   ├── src/
│   └── tests/
├── calc-engine/              # Rust calculation engine
│   ├── src/
│   │   ├── payroll/
│   │   ├── tax/
│   │   └── benefits/
│   └── tests/
├── extraction/               # PeopleSoft extraction tools
│   ├── parsers/             # PeopleCode parser
│   ├── transformers/        # Rule transformation
│   └── validators/          # Rule validation
├── compliance-agent/         # Regulatory monitoring
│   ├── sources/             # Source integrations
│   ├── parsers/             # Document parsers
│   └── workflows/           # Approval workflows
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── tests/
└── docs/
    ├── architecture/
    ├── rules/
    └── compliance/
```

---

## Conclusion

This architecture represents a fundamental shift in how HR systems operate:

1. **Rules are data** - Business logic is stored declaratively, not buried in code
2. **Agents are the runtime** - AI interprets and executes rules contextually
3. **Compliance is continuous** - Regulatory changes become data updates
4. **Everything is explainable** - The system can cite exactly why it made each decision
5. **Migration is gradual** - Extract and validate rules incrementally

The combination of extracted PeopleSoft business rules, AI agents for interpretation, and compiled engines for performance creates a system that is:

- **More maintainable** than traditional code
- **More auditable** than black-box systems
- **More adaptable** to regulatory changes
- **More explainable** to users and auditors

---

*Document version: 1.0*
*Last updated: 2026-02-28*

---
name: peopletools-diagrams
description: Generate UML and Mermaid diagrams from PeopleSoft metadata. Use when documenting PeopleSoft components, records, Application Engine programs, or data models with PlantUML or Mermaid.
---

# PeopleTools Diagram Documentation

Generate UML (PlantUML) and Mermaid diagrams from PeopleSoft metadata. Use MCP tools from user-peoplesoft to gather data, then apply the templates below.

## Workflow

1. **Gather metadata** via MCP tools: `get_record_definition`, `get_component_structure`, `get_page_fields`, `get_peoplecode`, `get_application_engine_steps`, `get_table_relationships`, `get_page_field_bindings`, `get_component_pages`.
2. **Choose diagram type** (ERD, component structure, AE flowchart).
3. **Apply template** from this skill or [examples.md](examples.md).
4. **Output** as markdown code block or write to `.md`/`.puml` file.

## Diagram Types

| Type | MCP Data Source | Output |
|------|-----------------|--------|
| Record ERD | get_record_definition, get_table_relationships | Mermaid ER / PlantUML class |
| Component structure | get_component_structure, get_page_fields | Mermaid flowchart / block |
| AE flowchart | get_application_engine_steps | Mermaid flowchart |

---

## Mermaid Templates

### Record ER Diagram

Records as entities; key fields in `{}`; relationships from `get_table_relationships` or shared keys.

```mermaid
erDiagram
    JOB ||--o{ JOB_CODE_TBL : "SETID_JOBCODE"
    JOB ||--o{ DEPT_TBL : "SETID_DEPT"
    JOB {
        string EMPLID PK
        number EMPL_RCD PK
        date EFFDT PK
        date EFFSEQ PK
        string DEPTID
        string COMPANY
    }
    DEPT_TBL {
        string SETID PK
        string DEPTID PK
        date EFFDT PK
        string DESCR
    }
```

### Component Structure (Hierarchy)

Component → pages → records from `get_component_structure` + `get_page_field_bindings` (distinct RECNAME per page).

```mermaid
flowchart TB
    subgraph COMPONENT["ABSV_PLAN_TABLE"]
        P1[ABSV_PLAN_TABLE]
    end
    P1 --> R1[ABSV_PLAN_TBL]
    P1 --> R2[BENEF_PLAN_TBL]
    P1 --> R3[ABSV_RATE_TBL]
    P1 --> R4[ABSV_ADDL_TBL]
```

### Application Engine Flowchart

Steps from `get_application_engine_steps`; use AE_SECTION, AE_STEP, DESCR. Mark PeopleCode vs SQL steps if available (from PSAESTMTDEFN).

```mermaid
flowchart LR
    subgraph MAIN["MAIN"]
        S1[Step01: initialization]
        S2[Step02: Delete]
        S1 --> S2
    end
```

---

## PlantUML Templates

### Record Class Diagram

```plantuml
@startuml
class JOB {
  +EMPLID : string [PK]
  +EMPL_RCD : number [PK]
  +EFFDT : date [PK]
  +EFFSEQ : date [PK]
  +DEPTID : string
  +COMPANY : string
}
class DEPT_TBL {
  +SETID : string [PK]
  +DEPTID : string [PK]
  +EFFDT : date [PK]
  +DESCR : string
}
JOB "1" --> "0..*" DEPT_TBL : SETID_DEPT
@enduml
```

### Component Structure

```plantuml
@startuml
package "ABSV_PLAN_TABLE" {
  [ABSV_PLAN_TABLE] as P1
}
P1 --> ABSV_PLAN_TBL
P1 --> BENEF_PLAN_TBL
P1 --> ABSV_RATE_TBL
P1 --> ABSV_ADDL_TBL
@enduml
```

---

## Conventions

- **Record names:** Use without PS_ prefix (JOB not PS_JOB) for consistency with metadata.
- **Key fields:** Mark with [PK] or place in `{}` for Mermaid ER.
- **Relationships:** Use shared key fields from `get_table_relationships` (relationship_strength, shared_key_fields).
- **Effective-dated:** Add EFFDT, EFFSEQ to key fields when RECTYPE indicates effective-dated table.
- **Scroll levels:** For component pages, OCCURSLEVEL from `get_page_field_bindings` indicates parent/child (0=level 0, 1=scroll 1, etc.).

## MCP Tool Mapping

| Need | Tool |
|------|------|
| Record fields, keys, type | get_record_definition |
| Related records by key | get_table_relationships |
| Component pages | get_component_structure or get_component_pages |
| Records per page | get_page_field_bindings or get_page_fields |
| AE steps, sections | get_application_engine_steps |
| PeopleCode events | get_peoplecode (for class diagram notes) |

## Additional Resources

- [examples.md](examples.md) — Full diagram examples
- [peopletools-mcp skill](../peopletools-mcp/SKILL.md) — MCP tool usage and fallbacks

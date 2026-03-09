# PeopleTools Diagram Examples

Full examples for each diagram type. Use these as templates when generating from MCP tool output.

---

## 1. Mermaid ER Diagram — JOB and Related Records

From `get_record_definition("JOB")`, `get_table_relationships("JOB")`, `get_record_definition` for related records.

```mermaid
erDiagram
    JOB ||--o{ DEPT_TBL : "SETID_DEPT"
    JOB ||--o{ COMPANY_TBL : "COMPANY"
    JOB ||--o{ JOBCODE_TBL : "SETID_JOBCODE"
    JOB ||--o{ LOCATION_TBL : "SETID_LOCATION"
    JOB {
        string EMPLID PK
        number EMPL_RCD PK
        date EFFDT PK
        date EFFSEQ PK
        string DEPTID FK
        string COMPANY FK
        string SETID_DEPT FK
        string JOBCODE FK
        string LOCATION FK
        string HR_STATUS
    }
    DEPT_TBL {
        string SETID PK
        string DEPTID PK
        date EFFDT PK
        string DESCR
    }
    COMPANY_TBL {
        string COMPANY PK
        date EFFDT PK
        string DESCR
    }
```

---

## 2. Mermaid Component Structure — JOB_DATA (12 pages)

From `get_component_structure("JOB_DATA")`, `get_page_field_bindings` for each page to get distinct records.

```mermaid
flowchart TB
    subgraph JOB_DATA["JOB_DATA - Job Data"]
        P1[JOB_DATA1]
        P2[JOB_DATA_EMPLMT]
        P3[JOB_DATA_COMP]
    end
    P1 --> JOB
    P1 --> EMPLMT_SRCH_ALL
    P2 --> JOB
    P3 --> COMPENSATION
```

---

## 3. Mermaid Component — Single Page with Scrolls (ABSV_PLAN_TABLE)

From `get_page_field_bindings("ABSV_PLAN_TABLE")` — OCCURSLEVEL indicates scroll (0=main, 1=scroll 1).

```mermaid
flowchart TB
    subgraph ABSV_PLAN_TABLE["ABSV_PLAN_TABLE - Vacation Plan"]
        P[ABSV_PLAN_TABLE]
    end
    P --> ABSV_PLAN_TBL
    P --> BENEF_PLAN_TBL
    P --> ABSV_RATE_TBL
    P --> ABSV_ADDL_TBL
    ABSV_PLAN_TBL -.->|"scroll 1"| ABSV_RATE_TBL
    ABSV_PLAN_TBL -.->|"scroll 2"| ABSV_ADDL_TBL
```

---

## 4. Mermaid AE Flowchart — GPES_TAX_10T

From `get_application_engine_steps("GPES_TAX_10T")` — MAIN section, Step01, Step02.

```mermaid
flowchart LR
    subgraph MAIN["MAIN"]
        S1[Step01: initialization]
        S2[Step02: Delete]
        S1 --> S2
    end
```

**With PeopleCode vs SQL:**
```mermaid
flowchart LR
    S1["Step01 (SQL Select)"]
    S2["Step02 (PeopleCode)"]
    S1 --> S2
```

---

## 5. PlantUML Class — Record with Key Fields

```plantuml
@startuml JOB_Record
skinparam classAttributeIconSize 0
class JOB {
  +EMPLID : string <<PK>>
  +EMPL_RCD : number <<PK>>
  +EFFDT : date <<PK>>
  +EFFSEQ : date <<PK>>
  +DEPTID : string
  +COMPANY : string
  +JOBCODE : string
  +HR_STATUS : string
}
note right of JOB
  Effective-dated
  Key: EMPLID, EMPL_RCD, EFFDT, EFFSEQ
end note
@enduml
```

---

## 6. PlantUML Component Package

```plantuml
@startuml DEPARTMENT_TBL
package "DEPARTMENT_TBL" {
  [DEPARTMENT_TBL_GBL] as GBL
  [DEPARTMENT_TBL_CA] as CA
  [ENCUMB_TRIGGER] as ENC
}
GBL --> DEPT_TBL
GBL --> DERIVED_ORGCHRT
CA --> DEPT_TBL
ENC --> ENCUMB_TRIGGER
@enduml
```

---

## 7. Mermaid Sequence — PeopleCode Event Flow (Optional)

From `get_peoplecode(record_name)` — show event order (RowInit → FieldChange → SaveEdit).

```mermaid
sequenceDiagram
    participant DB as Database
    participant PC as PeopleCode
    participant UI as Page

    DB->>PC: RowSelect
    PC->>UI: RowInit
    UI->>PC: FieldChange (user edit)
    PC->>UI: FieldFormula
    UI->>PC: SaveEdit
    PC->>DB: SavePreChange / SavePostChange
```

---

## Tips

- **Truncate large diagrams:** Limit to 5–10 records per ERD; 3–5 pages per component.
- **Focus:** For impact analysis, show only key records and relationships.
- **File output:** Write to `docs/diagrams/<component>_<type>.md` for version control.

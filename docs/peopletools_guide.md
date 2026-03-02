# PeopleTools Architecture Guide

This guide explains PeopleTools - the technology platform that powers PeopleSoft applications. Understanding PeopleTools helps you navigate and customize the system.

## Overview

PeopleTools provides:
- **Application Designer**: Development environment for pages, records, PeopleCode
- **Data Mover**: Import/export of data and definitions
- **Application Engine**: Batch processing framework
- **Integration Broker**: Web services and messaging
- **Process Scheduler**: Job scheduling and execution
- **Query Manager**: Ad-hoc reporting tool

---

## Record Types

PeopleSoft organizes data using "records" which may or may not be physical database tables.

| Type | Value | Description | Database Object |
|------|-------|-------------|-----------------|
| SQL Table | 0 | Physical database table | Yes - CREATE TABLE |
| SQL View | 1 | Database view | Yes - CREATE VIEW |
| Derived/Work | 2 | Runtime-only record | No |
| Sub Record | 3 | Reusable field group | No |
| Dynamic View | 5 | View with bind variables | Yes |
| Query View | 6 | Generated from PS Query | Yes |
| Temp Table | 7 | App Engine temporary table | Yes (multiple instances) |

### Metadata Tables for Records

```sql
-- Get all record definitions
SELECT RECNAME, RECTYPE, RECDESCR FROM PSRECDEFN WHERE RECNAME = 'JOB'

-- Get fields in a record
SELECT FIELDNAME, FIELDNUM, USEEDIT FROM PSRECFIELD WHERE RECNAME = 'JOB' ORDER BY FIELDNUM

-- Get field properties
SELECT FIELDNAME, FIELDTYPE, LENGTH, DECIMALPOS FROM PSDBFIELD WHERE FIELDNAME = 'EMPLID'

-- Get key fields
SELECT FIELDNAME, KEYPOSN FROM PSKEYDEFN WHERE RECNAME = 'JOB' ORDER BY KEYPOSN
```

---

## Pages and Components

### Pages (PSPNLDEFN)
A page is a single screen in the application. Pages contain fields bound to records.

```sql
-- Get page definition
SELECT PNLNAME, DESCR, PNLTYPE FROM PSPNLDEFN WHERE PNLNAME = 'JOB_DATA1'

-- Get fields on a page
SELECT FIELDNUM, RECNAME, FIELDNAME, LBLTEXT 
FROM PSPNLFIELD 
WHERE PNLNAME = 'JOB_DATA1'
ORDER BY FIELDNUM
```

### Components (PSPNLGRPDEFN)
A component is a collection of pages that work together. Components define the transaction.

```sql
-- Get component definition
SELECT PNLGRPNAME, DESCR, SEARCHRECNAME, MARKET 
FROM PSPNLGRPDEFN 
WHERE PNLGRPNAME = 'JOB_DATA'

-- Get pages in a component
SELECT PNLNAME, ITEMNUM, ITEMLABEL 
FROM PSPNLGROUP 
WHERE PNLGRPNAME = 'JOB_DATA' 
ORDER BY ITEMNUM
```

### Navigation Path
```sql
-- Find where a component appears in menus
SELECT MENUNAME, BARNAME, BARITEMNAME, ITEMLABEL, PNLGRPNAME 
FROM PSMENUITEM 
WHERE PNLGRPNAME = 'JOB_DATA'
```

---

## PeopleCode Events

PeopleCode can be attached to various objects at different events.

### Record/Field Events
| Event | When It Fires |
|-------|---------------|
| RowInit | When a row is read from the database |
| RowInsert | When a new row is added |
| FieldChange | When a field value changes |
| FieldEdit | Validates field before save |
| FieldFormula | For calculated fields |
| FieldDefault | Sets default value |
| SaveEdit | Validates before saving |
| SavePreChange | Just before database update |
| SavePostChange | After database update |
| RowDelete | When a row is deleted |

### Component Events
| Event | When It Fires |
|-------|---------------|
| SearchInit | Before search page displays |
| SearchSave | When user clicks Search |
| PreBuild | Before component buffer builds |
| PostBuild | After component loads completely |
| SavePreChange | Before component saves |
| SavePostChange | After component saves |
| Workflow | For workflow routing |

```sql
-- Find PeopleCode on a record
SELECT RECNAME, FIELDNAME, EVENT, LASTUPDOPRID 
FROM PSPCMPROG 
WHERE RECNAME = 'JOB' 
ORDER BY FIELDNAME, EVENT

-- Search for text in PeopleCode
SELECT RECNAME, FIELDNAME, EVENT 
FROM PSPCMPROG 
WHERE UPPER(PROGTXT) LIKE '%CREATEROWSET%'

-- Get actual PeopleCode source (CLOB handling)
SELECT OBJECTVALUE1 AS RECORD, OBJECTVALUE2 AS FIELD, OBJECTVALUE3 AS EVENT,
       DBMS_LOB.SUBSTR(PCTEXT, 4000, 1) AS PEOPLECODE
FROM PSPCMTXT
WHERE OBJECTID1 = 1 AND OBJECTVALUE1 = 'JOB'
ORDER BY OBJECTVALUE2, OBJECTVALUE3
```

---

## PeopleCode Execution Order

Understanding when PeopleCode fires is critical for debugging and development. Events fire in a specific, predictable sequence.

### Component Open Sequence

When a user opens a component (transaction), events fire in this order:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SEARCH PAGE PHASE                           │
├─────────────────────────────────────────────────────────────────┤
│  1. SearchInit (Component)                                      │
│     └── Manipulate search page, set defaults, hide fields       │
│                                                                 │
│  2. SearchSave (Component)                                      │
│     └── Validate/modify search criteria before SQL executes     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LOADING PHASE                          │
├─────────────────────────────────────────────────────────────────┤
│  3. RowSelect (Record.Field)                                    │
│     └── Fires for EACH row selected, can reject rows            │
│                                                                 │
│  For each row loaded (scroll level 0, then 1, then 2...):       │
│                                                                 │
│  4. FieldDefault (Record.Field)                                 │
│     └── Set default values for NEW rows only                    │
│                                                                 │
│  5. FieldFormula (Record.Field)                                 │
│     └── Calculate derived field values                          │
│                                                                 │
│  6. RowInit (Record.Field)                                      │
│     └── Initialize row, set field properties (Gray, Hide, etc.) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    COMPONENT BUILD PHASE                        │
├─────────────────────────────────────────────────────────────────┤
│  7. PreBuild (Component)                                        │
│     └── Before page displays, modify buffer/UI                  │
│                                                                 │
│  8. PostBuild (Component)                                       │
│     └── Component fully loaded, final UI adjustments            │
└─────────────────────────────────────────────────────────────────┘
```

### Field Interaction Sequence

When a user changes a field value:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. FieldEdit (Record.Field)                                    │
│     └── VALIDATE the new value                                  │
│     └── Use Error/Warning to reject invalid values              │
│     └── Fires BEFORE value is accepted into buffer              │
│                                                                 │
│  2. FieldChange (Record.Field)                                  │
│     └── PROCESS the change                                      │
│     └── Update related fields, call functions                   │
│     └── Fires AFTER value is in buffer                          │
│                                                                 │
│  3. FieldFormula (Record.Field) - if other fields affected      │
│     └── Recalculate derived values                              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Difference: FieldEdit vs FieldChange**
- `FieldEdit`: Validation - use `Error` to reject value, field stays in edit mode
- `FieldChange`: Processing - value already accepted, update other fields

### Save Processing Sequence

When user clicks Save, events fire in this precise order:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│  1. SaveEdit (Record.Field) - ALL levels, ALL rows              │
│     └── Final validation before save                            │
│     └── Error here STOPS the save                               │
│     └── Fires: Level 0 → Level 1 → Level 2 (top to bottom)      │
│                                                                 │
│  2. SaveEdit (Component)                                        │
│     └── Component-level validation                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-SAVE PHASE                               │
├─────────────────────────────────────────────────────────────────┤
│  3. SavePreChange (Record.Field) - for CHANGED rows only        │
│     └── Last chance to modify data before SQL                   │
│     └── Set audit fields, derived values                        │
│     └── Database NOT yet updated                                │
│                                                                 │
│  4. SavePreChange (Component)                                   │
│     └── Component-level pre-save logic                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE UPDATE                              │
│         (INSERT/UPDATE/DELETE SQL executes here)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    POST-SAVE PHASE                              │
├─────────────────────────────────────────────────────────────────┤
│  5. Workflow (Component)                                        │
│     └── Workflow routing, if enabled                            │
│                                                                 │
│  6. SavePostChange (Record.Field) - for CHANGED rows only       │
│     └── After commit - trigger integrations, messages           │
│     └── Data IS committed at this point                         │
│                                                                 │
│  7. SavePostChange (Component)                                  │
│     └── Final component-level processing                        │
└─────────────────────────────────────────────────────────────────┘
```

### Row-Level Event Order

**When a NEW row is inserted:**
```
FieldDefault → FieldFormula → RowInit → RowInsert
```

**When a row is DELETED:**
```
RowDelete (fires BEFORE row is removed from buffer)
└── Return Error to prevent deletion
```

**Processing order across scroll levels:**
```
Level 0 (parent)
  └── Level 1 (child rows)
        └── Level 2 (grandchild rows)
```

### Deferred Processing Mode

Some components use "deferred processing" to improve performance:

```sql
-- Check if component uses deferred processing
SELECT PNLGRPNAME, DEFERPROC FROM PSPNLGRPDEFN WHERE PNLGRPNAME = 'JOB_DATA'
```

**With Deferred Processing:**
- FieldEdit/FieldChange don't fire immediately on field exit
- Events are "batched" until user clicks a button or changes focus significantly
- Use `DoSaveNow()` to force immediate processing

### Event Firing Summary Table

| Phase | Event | Level | Fires For |
|-------|-------|-------|-----------|
| Search | SearchInit | Component | Once on search page load |
| Search | SearchSave | Component | Once when Search clicked |
| Load | RowSelect | Record.Field | Each row from SQL |
| Load | FieldDefault | Record.Field | New rows only |
| Load | FieldFormula | Record.Field | Calculated fields |
| Load | RowInit | Record.Field | Every row loaded |
| Load | PreBuild | Component | Once before display |
| Load | PostBuild | Component | Once after display |
| Edit | FieldEdit | Record.Field | On field value change |
| Edit | FieldChange | Record.Field | After value accepted |
| Edit | RowInsert | Record.Field | New row added |
| Edit | RowDelete | Record.Field | Row being deleted |
| Save | SaveEdit | Record.Field | All changed rows |
| Save | SaveEdit | Component | Once |
| Save | SavePreChange | Record.Field | Changed rows only |
| Save | SavePreChange | Component | Once |
| Save | Workflow | Component | If workflow enabled |
| Save | SavePostChange | Record.Field | Changed rows only |
| Save | SavePostChange | Component | Once |

### Common Patterns

**Set field as required based on another field:**
```peoplecode
/* In FieldChange of controlling field */
If RECORD.STATUS = "A" Then
   SetRequired(RECORD.EFFECTIVE_DATE);
Else
   SetRequired(RECORD.EFFECTIVE_DATE, False);
End-If;
```

**Gray/Ungray fields based on mode:**
```peoplecode
/* In RowInit */
If %Mode = "U" Then  /* Update mode */
   Gray(RECORD.KEY_FIELD);
Else
   UnGray(RECORD.KEY_FIELD);
End-If;
```

**Prevent deletion of approved records:**
```peoplecode
/* In RowDelete */
If RECORD.APPROVED_FLAG = "Y" Then
   Error MsgGet(1000, 1, "Cannot delete approved records");
End-If;
```

**Cross-validate in SaveEdit:**
```peoplecode
/* In SaveEdit */
If RECORD.END_DATE < RECORD.BEGIN_DATE Then
   Error MsgGet(1000, 2, "End date must be after begin date");
End-If;
```

---

## Security Model

### Hierarchy
```
User (PSOPRDEFN)
  └── Roles (PSROLEUSER)
        └── Permission Lists (PSROLECLASS)
              └── Component Access (PSAUTHITEM)
              └── Page Access (PSAUTHPAGE)
              └── Query Access (PSQRYACCLST)
```

### Key Security Tables

```sql
-- Find user's roles
SELECT OPRID, ROLENAME FROM PSROLEUSER WHERE OPRID = 'PS'

-- Find permission lists in a role
SELECT ROLENAME, CLASSID FROM PSROLECLASS WHERE ROLENAME = 'PeopleSoft Administrator'

-- Find component access in a permission list
SELECT CLASSID, MENUNAME, PNLGRPNAME, MARKET, AUTHVALUE 
FROM PSAUTHITEM 
WHERE CLASSID = 'ALLPANLS'

-- Find who can access a component
SELECT DISTINCT A.CLASSID AS PERMISSION_LIST, RC.ROLENAME, RU.OPRID
FROM PSAUTHITEM A
JOIN PSROLECLASS RC ON A.CLASSID = RC.CLASSID
JOIN PSROLEUSER RU ON RC.ROLENAME = RU.ROLENAME
WHERE A.PNLGRPNAME = 'JOB_DATA'
```

---

## Process Scheduler

### Process Types
| Type | Description |
|------|-------------|
| SQR Report | SQR programs |
| Application Engine | PeopleSoft batch programs |
| COBOL SQL | COBOL programs |
| Crystal | Crystal Reports |
| Data Mover | Data Mover scripts |
| nVision | Excel-based reporting |

### Key Tables

```sql
-- Process definitions
SELECT PRCSTYPE, PRCSNAME, DESCR 
FROM PS_PRCSDEFN 
WHERE PRCSTYPE = 'Application Engine'

-- Process request history
SELECT PRCSINSTANCE, PRCSTYPE, PRCSNAME, RUNSTATUS, BEGINDTTM, ENDDTTM
FROM PSPRCSRQST
ORDER BY PRCSINSTANCE DESC
FETCH FIRST 20 ROWS ONLY

-- Run status values: 1=Queued, 7=Processing, 9=Success, 10=No Success
```

---

## Application Engine

Application Engine is PeopleSoft's batch processing framework.

### Structure
```
Program (AE_APPLID)
  └── Sections (AE_SECTION)
        └── Steps (AE_STEP)
              └── Actions (SQL, PeopleCode, Call Section, Do Select, etc.)
```

### Key Tables

```sql
-- AE Program definitions
SELECT AE_APPLID, DESCR FROM PSAEAPPLDEFN

-- AE Sections and Steps
SELECT AE_APPLID, AE_SECTION, AE_STEP, AE_STEP_NBR 
FROM PSAESTEPDEFN 
WHERE AE_APPLID = 'MY_PROGRAM'
ORDER BY AE_SECTION, AE_STEP_NBR

-- Temp tables used by AE
SELECT DISTINCT AE_APPLID, RECNAME 
FROM PSAETEMPTBLUSE 
WHERE AE_APPLID = 'MY_PROGRAM'
```

---

## Integration Broker

Integration Broker handles web services, messages, and integrations.

### Key Concepts
- **Service**: Collection of operations (like a web service)
- **Operation**: A single request/response transaction
- **Message**: The data structure sent/received
- **Routing**: How messages get to their destination

### Key Tables

```sql
-- Service operations
SELECT IB_SERVICE, IB_OPERATIONNAME, IB_OPERATIONTYPE, REQUESTMSGNAME
FROM PSOPERATION
WHERE IB_SERVICE = 'HR_PERSON_DATA'

-- Message definitions
SELECT MSGNAME, DESCR, VERSION FROM PSMSGDEFN WHERE MSGNAME = 'HR_PERSON_DATA_SYNC'

-- Message parts (records in the message)
SELECT MSGNAME, PARTNAME, RECNAME FROM PSMSGPARTDEFN WHERE MSGNAME = 'HR_PERSON_DATA_SYNC'

-- Routing definitions
SELECT * FROM PSMSGROUT WHERE IBOPERATIONNAME = 'HR_PERSON_DATA_SYNC'
```

---

## Query Manager

PS Query allows ad-hoc reporting without writing SQL.

### Key Tables

```sql
-- Query definitions
SELECT QRYNAME, DESCR, OPRID, QRYTYPE FROM PSQRYDEFN

-- Query records
SELECT QRYNAME, RECNAME, CORRNAME FROM PSQRYRECORD WHERE QRYNAME = 'MY_QUERY'

-- Query fields
SELECT QRYNAME, RECNAME, FIELDNAME, HEADING FROM PSQRYFIELD WHERE QRYNAME = 'MY_QUERY'

-- Query access
SELECT QRYNAME, CLASSID, ACCESSLVL FROM PSQRYACCLST WHERE QRYNAME = 'MY_QUERY'
```

---

## SQL Objects (PSSQLTEXTDEFN)

PeopleSoft stores SQL text for views, Application Engine programs, PeopleCode (SQL.SQLID), and other objects in PSSQLTEXTDEFN. Long SQL is split across rows by SEQNUM.

### Key Table

```sql
-- Get SQL text by SQLID
SELECT SQLID, SQLTYPE, MARKET, SEQNUM, DBMS_LOB.SUBSTR(SQLTEXT, 14000, 1) AS SQLTEXT
FROM PSSQLTEXTDEFN
WHERE SQLID = 'HR_ABSV_JOB_EFFDT'
ORDER BY SEQNUM

-- Search for SQL objects referencing a table
SELECT DISTINCT SQLID, SQLTYPE, MARKET
FROM PSSQLTEXTDEFN
WHERE DBMS_LOB.INSTR(SQLTEXT, 'PS_JOB') > 0
```

**MCP tools**: Use `get_sql_definition` and `search_sql_definitions` for structured access.

---

## Common Development Tasks

### Finding Where a Field is Used
```sql
-- Which records use this field?
SELECT RECNAME FROM PSRECFIELD WHERE FIELDNAME = 'EMPLID' ORDER BY RECNAME

-- Which pages display this field?
SELECT PNLNAME, RECNAME, FIELDNAME FROM PSPNLFIELD WHERE FIELDNAME = 'EMPLID'

-- Is there PeopleCode on this field?
SELECT RECNAME, FIELDNAME, EVENT FROM PSPCMPROG WHERE FIELDNAME = 'EMPLID'
```

### Finding Where a Record is Used
```sql
-- Which components use this record?
SELECT DISTINCT P.PNLGRPNAME
FROM PSPNLFIELD PF
JOIN PSPNLGROUP P ON PF.PNLNAME = P.PNLNAME
WHERE PF.RECNAME = 'JOB'

-- Which Application Engines use this record?
SELECT DISTINCT AE_APPLID FROM PSAESTEPMSGDEFN WHERE UPPER(AE_PEOPLECODEPC) LIKE '%JOB%'
```

### Impact Analysis
```sql
-- What might break if I change this field?
SELECT 'Record' AS OBJECT_TYPE, RECNAME AS OBJECT_NAME FROM PSRECFIELD WHERE FIELDNAME = 'MY_FIELD'
UNION ALL
SELECT 'Page', PNLNAME FROM PSPNLFIELD WHERE FIELDNAME = 'MY_FIELD'
UNION ALL
SELECT 'PeopleCode', RECNAME || '.' || EVENT FROM PSPCMPROG WHERE FIELDNAME = 'MY_FIELD'
```

---

## Useful Tips

1. **All objects are in metadata tables** - You can query them to understand the system
2. **RECNAME doesn't have PS_ prefix** - The table might be PS_JOB but RECNAME is just 'JOB'
3. **Use PSKEYDEFN for indexes** - Shows you how to query efficiently
4. **Check PSXLATITEM for codes** - Most short codes have translations
5. **Component = Unit of work** - Pages are just views, components define transactions
6. **Security is additive** - Users get the union of all their permission lists

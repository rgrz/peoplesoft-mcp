---
name: peopletools-mcp
description: Use and extend the PeopleSoft MCP server. Use when working with PeopleSoft databases, MCP tools (get_record_definition, get_peoplecode, query_peoplesoft_db), PeopleTools metadata, or proposing enhancements to tools/peopletools.py.
---

# PeopleTools MCP

Guide for using the PeopleSoft MCP server and proposing enhancements. MCP tools live in `tools/peopletools.py`; the server is `peoplesoft_server.py`.

## Tool Selection

**Reliable (use first):**
- `get_record_definition(record_name)` — fields, keys, types
- `get_peoplecode(record_name, field_name?, event?, include_code?)` — PeopleCode from PSPCMTXT
- `query_peoplesoft_db(sql_query, parameters?)` — raw SQL fallback
- `describe_table(table_name)` — field list for metadata tables

**May fail (PeopleTools version differences):** `get_component_structure`, `get_page_fields`, `get_application_engine_steps` reference columns that vary by PT version (SAVEWARN, ITEMNUM vs SUBITEMNUM, AE_STEP_NBR vs AE_SEQ_NUM, DSPCTLFLDNAME, etc.).

**Fallback:** When a semantic tool errors, use `query_peoplesoft_db` with `describe_table` first to confirm column names. Proven patterns in [reference.md](reference.md).

## Component Exploration Workflow

For a component (e.g., ABSV_REQUEST):

1. **Record:** `get_record_definition("ABSV_REQUEST")`
2. **PeopleCode:** `get_peoplecode("ABSV_REQUEST")`
3. **Component/Pages:** If `get_component_structure` fails, use:

```sql
SELECT PNLGRPNAME, DESCR, SEARCHRECNAME FROM PSPNLGRPDEFN WHERE PNLGRPNAME = 'ABSV_REQUEST';
SELECT PNLNAME, SUBITEMNUM, ITEMLABEL FROM PSPNLGROUP WHERE PNLGRPNAME = 'ABSV_REQUEST' ORDER BY SUBITEMNUM;
```

4. **Page fields:** If `get_page_fields` fails:

```sql
SELECT RECNAME, FIELDNAME, FIELDNUM FROM PSPNLFIELD WHERE PNLNAME = 'ABSV_REQUEST' ORDER BY FIELDNUM;
```

## MCP Resources

Use `fetch_mcp_resource` with `user-peoplesoft` for:
- `peoplesoft://peopletools-guide` — records, pages, PeopleCode events, security, AE, IB
- `peoplesoft://schema-guide` — tables by module (HR, Payroll, Benefits, etc.)
- `peoplesoft://concepts` — effective dating, EMPLID, SetID
- `peoplesoft://query-examples` — SQL patterns with effective dating

## Proposing Enhancements

When a tool fails or a new capability would help:

1. **Identify the metadata tables** — See [peopletools-tables-by-tool.md](../../docs/peopletools-tables-by-tool.md)
2. **Check schema** — Use `describe_table("PSPNLGRPDEFN")` (or target table) to verify column names
3. **Minimize column dependencies** — Prefer widely available columns; avoid SAVEWARN, DSPCTLFLDNAME, AE_STEP_NBR, ITEMNUM
4. **Add to tools/peopletools.py** — Follow existing patterns (normalize record names, handle LOBs via DBMS_LOB)
5. **Register in register_tools()** — Add `mcp.tool()(new_function)`

**Implemented:** `get_component_pages`, `get_page_field_bindings` (version-safe, lightweight).  
**Future:** `get_ae_structure`, version detection for SQL variants.
- Version detection to choose SQL variants

## Key PeopleTools Tables

| Table | Purpose |
|-------|---------|
| PSRECDEFN, PSRECFIELD | Record definitions |
| PSPNLGRPDEFN, PSPNLGROUP | Components and pages |
| PSPNLDEFN, PSPNLFIELD | Page definitions and field bindings |
| PSPCMTXT | PeopleCode source (CLOB) |
| PSAEAPPLDEFN, PSAESTEPDEFN | Application Engine |
| PSSQLTEXTDEFN | SQL objects |
| PSXLATITEM | Translate values |

RECNAME in metadata omits PS_ prefix (JOB → PS_JOB).

## Additional Resources

- [reference.md](reference.md) — Verified column names, fallback queries, enhancement checklist
- [docs/peopletools_guide.md](../../docs/peopletools_guide.md) — PeopleCode events, security model
- [docs/mcp-tools-experiment-report.md](../../docs/mcp-tools-experiment-report.md) — Tool status by environment

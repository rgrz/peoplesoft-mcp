# PeopleTools MCP Reference

Fallback queries and enhancement patterns when semantic tools fail due to PeopleTools version differences.

## Verified Fallback Queries

### Component Structure (when get_component_structure fails)

```sql
-- Component header
SELECT PNLGRPNAME, DESCR, MARKET, SEARCHRECNAME, ADDSRCHRECNAME 
FROM PSPNLGRPDEFN WHERE PNLGRPNAME = :component_name;

-- Pages (use SUBITEMNUM not ITEMNUM)
SELECT P.PNLNAME, P.SUBITEMNUM, P.HIDDEN, P.ITEMLABEL, PD.DESCR 
FROM PSPNLGROUP P 
LEFT JOIN PSPNLDEFN PD ON P.PNLNAME = PD.PNLNAME 
WHERE P.PNLGRPNAME = :component_name ORDER BY P.SUBITEMNUM;
```

### Page Fields (when get_page_fields returns empty)

```sql
SELECT F.FIELDNUM, F.FIELDTYPE, F.RECNAME, F.FIELDNAME, F.LBLTEXT, F.OCCURSLEVEL
FROM PSPNLFIELD F 
WHERE F.PNLNAME = :page_name
ORDER BY F.OCCURSLEVEL, F.FIELDNUM;
```

### Application Engine Steps (when get_application_engine_steps fails)

```sql
SELECT S.AE_SECTION, S.AE_STEP, S.AE_SEQ_NUM, S.AE_ACTIVE_STATUS
FROM PSAESTEPDEFN S 
WHERE S.AE_APPLID = :ae_program
ORDER BY S.AE_SECTION, S.AE_SEQ_NUM;
```

## Column Name Variants by PT Version

| Table | Problematic Columns | Version-Safe Alternatives |
|-------|---------------------|---------------------------|
| PSPNLGRPDEFN | SAVEWARN (may not exist) | Omit; use DESCR, SEARCHRECNAME |
| PSPNLGROUP | ITEMNUM | SUBITEMNUM (alias as ITEMNUM in output) |
| PSPNLFIELD | DSPCTLFLDNAME, DSPCNTRLRECNAME | Use RECNAME, FIELDNAME, FIELDNUM, LBLTEXT, OCCURSLEVEL |
| PSAESTEPDEFN | AE_STEP_NBR | AE_SEQ_NUM |
| PSAESTEPDEFN | AE_SQL_FLAG, AE_DO_FLAG, AE_CMD_BTN_ENABLED | STEP_DESCR or AE_ACTIVE_STATUS |

## Enhancement Checklist

When adding or fixing a tool in `tools/peopletools.py`:

1. [ ] Use `describe_table` against target tables in target env to verify columns
2. [ ] Prefer columns from "Version-Safe Alternatives" table above
3. [ ] For CLOBs (PSPCMTXT, PSSQLTEXTDEFN, PSDBFIELD.DESCRLONG): use `DBMS_LOB.SUBSTR(col, len, 1)`
4. [ ] Normalize record names: strip PS_ prefix, uppercase
5. [ ] Handle "not found" gracefully: return `{"error": "..."}` not exception
6. [ ] Add to `register_tools(mcp)` in peopletools.py
7. [ ] Restart MCP server for changes to take effect

## Tool → Table Dependencies

From `docs/peopletools-tables-by-tool.md` — each tool requires SELECT on:

- get_record_definition: PSRECDEFN, PSRECFIELD, PSDBFIELD, PSKEYDEFN, PSINDEXDEFN
- get_component_structure: PSPNLGRPDEFN, PSPNLGROUP, PSPNLDEFN, PSMENUITEM
- get_component_pages: PSPNLGRPDEFN, PSPNLGROUP (lightweight alternative)
- get_page_fields: PSPNLDEFN, PSPNLFIELD
- get_page_field_bindings: PSPNLDEFN, PSPNLFIELD (RECNAME, FIELDNAME, FIELDNUM, OCCURSLEVEL)
- get_peoplecode: PSPCMTXT
- get_application_engine_steps: PSAEAPPLDEFN, PSAESTEPDEFN

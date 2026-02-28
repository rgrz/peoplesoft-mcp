# PeopleSoft HR Migration Analysis

Analysis of using the PeopleSoft MCP for migrating PeopleSoft HR to a modern stack (Python/Rust).

## Current MCP Capabilities (Migration Value)

| Capability | Migration Value | Status |
|------------|-----------------|--------|
| Schema introspection | Generate data models (SQLAlchemy, Diesel) | ✅ Ready |
| PeopleCode extraction | Understand business logic to reimplement | ✅ Ready |
| Table relationships/keys | Design foreign keys, indexes | ✅ Ready |
| Translate values | Create enum types / lookup tables | ✅ Ready |
| Component structure | Understand UI flows for new frontend | ✅ Ready |
| Execution order docs | Reimplement event-driven logic correctly | ✅ Ready |

**Current coverage: ~40-50% of migration needs**

---

## Gaps for Real Migration

### 1. Business Rule Extraction

The PeopleCode is readable, but needs *parsing and analysis* to extract:
- Validation rules → convert to Python/Rust validators
- Default value logic → convert to model defaults
- Calculated fields → convert to computed properties
- Cross-field validations → convert to model validators

### 2. USEEDIT Decoder

The `USEEDIT` field in PSRECFIELD is a bitmask encoding field-level edits:
- Required field
- Yes/No values only
- Uppercase conversion
- Reasonable date range
- Prompt table edit

A tool to decode this would auto-generate field constraints.

### 3. Application Engine SQL/Logic

Currently we get AE structure, but not the actual SQL statements in each step. Those contain critical batch processing logic stored in `PSAESQLDEFN`.

### 4. Workflow/Approval Chains

PeopleSoft Workflow (AWE) has complex approval routing:
- Approval step definitions
- Routing criteria
- Escalation rules
- Stored in EOAW* tables

### 5. Integration Mappings

What external systems connect:
- Field mappings
- Transformation logic
- Message schemas
- Stored in IB tables (PSOPERATION, PSMSGDEFN, etc.)

### 6. Customization Identifier

Distinguish Oracle-delivered vs customer-modified objects:
- Check OBJECTOWNERID patterns
- Check LASTUPDOPRID for customer operators
- Compare against vanilla baseline

---

## Proposed MCP Additions

### New Tools

```python
# Decode USEEDIT bitmask → field constraints
get_useedit_rules(record_name: str) -> dict

# Extract actual SQL from AE steps
get_ae_sql_statements(ae_program: str) -> dict

# Extract AWE approval chains
get_workflow_definition(approval_id: str) -> dict

# Parse PeopleCode → structured rules
analyze_peoplecode(record: str, field: str) -> dict

# Find customer-modified objects
get_customizations(module: str) -> dict

# Diff against Oracle baseline
compare_to_vanilla(record_name: str) -> dict
```

### Rules (`.cursor/rules/`)

| Rule File | Purpose |
|-----------|---------|
| `migration-patterns.mdc` | How to map PS concepts → Python/Rust |
| `naming-conventions.mdc` | PS field names → Python/Rust naming |
| `effective-date-pattern.mdc` | Standard pattern for temporal tables |
| `security-mapping.mdc` | PS security → new auth model |

### Skills (`.cursor/skills-cursor/`)

| Skill | Purpose |
|-------|---------|
| `generate-sqlalchemy-models/` | PS record → SQLAlchemy model |
| `generate-rust-structs/` | PS record → Rust struct + Diesel |
| `generate-pydantic-schemas/` | PS record → Pydantic validation |
| `generate-api-endpoints/` | PS component → FastAPI/Axum routes |
| `extract-business-rules/` | PeopleCode → structured rule JSON |

---

## Migration Phases

### Phase 1: Schema Migration (MCP handles well)
- Extract all records, fields, keys, relationships
- Generate target data models
- Migrate lookup/translate tables

### Phase 2: Business Logic Extraction (MCP partially helps)
- Extract all PeopleCode
- Categorize by type (validation, default, calculation)
- Prioritize by complexity/usage

### Phase 3: Logic Reimplementation (Need skills/templates)
- Simple validations → auto-generate
- Complex logic → manual with AI assistance
- Test with production data samples

### Phase 4: UI/API Layer (Need new tools)
- Map components to API endpoints
- Design new frontend or headless API

---

## Key PeopleSoft Tables for Migration

### Schema/Metadata
- `PSRECDEFN` - Record definitions
- `PSRECFIELD` - Fields in records (includes USEEDIT)
- `PSDBFIELD` - Field properties
- `PSKEYDEFN` - Key/index definitions

### PeopleCode
- `PSPCMTXT` - PeopleCode source (CLOB)
- `PSPCMPROG` - PeopleCode metadata

### Components/Pages
- `PSPNLGRPDEFN` - Component definitions
- `PSPNLGROUP` - Pages in components
- `PSPNLDEFN` - Page definitions
- `PSPNLFIELD` - Fields on pages

### Application Engine
- `PSAEAPPLDEFN` - AE program header
- `PSAESECTDEFN` - AE sections
- `PSAESTEPDEFN` - AE steps
- `PSAESQLDEFN` - AE SQL statements
- `PSAESTEPMSGDEFN` - AE PeopleCode

### Security
- `PSOPRDEFN` - Users
- `PSROLEDEFN` - Roles
- `PSROLEUSER` - User-Role mapping
- `PSROLECLASS` - Role-Permission List mapping
- `PSCLASSDEFN` - Permission Lists
- `PSAUTHITEM` - Component access

### Workflow (AWE)
- `EOAWDEFN` - Approval definitions
- `EOAWSTEP` - Approval steps
- `EOAWCRTRA` - Approval criteria

---

## Estimated Effort Distribution

| Phase | Effort | Automation Potential |
|-------|--------|---------------------|
| Schema extraction | 10% | 90% automated |
| Data model generation | 15% | 80% automated |
| Business rule extraction | 25% | 50% automated |
| Logic reimplementation | 30% | 30% automated |
| Testing/validation | 20% | 40% automated |

---

## Next Steps

1. Add USEEDIT decoder tool
2. Add AE SQL extraction tool
3. Create code generation skills
4. Build PeopleCode parser for rule extraction
5. Create comparison/validation framework

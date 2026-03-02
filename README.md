# PeopleSoft MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to query and understand PeopleSoft HCM databases. This server provides semantic tools for HR, Payroll, Benefits, Performance, and PeopleTools metadata - allowing natural language questions to be answered with accurate SQL queries.

## Features

- **41 semantic tools** covering all major PeopleSoft HCM modules
- **4 documentation resources** for PeopleSoft concepts and query patterns
- **Direct database access** via Oracle thin client (no JDBC required)
- **PeopleTools introspection** for understanding system architecture
- **Effective dating support** built into all queries

## Quick Start

### Prerequisites

- Python 3.11+
- Oracle Database connectivity to a PeopleSoft HCM 9.2 instance
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd peoplesoft-mcp

# Install dependencies
uv sync
```

### Configuration

1. Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```

2. Edit `.env` with your database credentials:
```bash
ORACLE_DSN=hostname:port/service_name
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
```

3. Edit `.cursor/peoplesoft-mcp.json` and update the path to your installation.

### Running the Server

```bash
uv run peoplesoft_server.py
```

### Cursor IDE Integration

The MCP config (`.cursor/peoplesoft-mcp.json`) should look like:

```json
{
  "mcpServers": {
    "peoplesoft": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp_ps/",
        "run",
        "peoplesoft_server.py"
      ]
    }
  }
}
```

Credentials are loaded from `.env` automatically - no need to include them in the MCP config.

## Available Tools

### Schema Introspection (5 tools)
| Tool | Description |
|------|-------------|
| `describe_table` | Get table structure, fields, and indexes |
| `list_tables` | Search for tables by name pattern |
| `get_translate_values` | Decode field codes (XLAT values) |
| `get_table_indexes` | View index definitions for performance |
| `get_table_relationships` | Find foreign key relationships |

### HR Module (5 tools)
| Tool | Description |
|------|-------------|
| `get_employee` | Get employee details by EMPLID |
| `search_employees` | Search employees by name, department, etc. |
| `get_job_history` | View job history for an employee |
| `get_org_chart` | Get organizational hierarchy |
| `get_department_info` | Get department details and headcount |

### Payroll Module (5 tools)
| Tool | Description |
|------|-------------|
| `get_payroll_results` | View payroll calculation results |
| `get_payroll_status` | Check payroll processing status |
| `get_accumulator_balances` | Get YTD/MTD balances |
| `get_payment_info` | Get payment details |
| `list_calendar_runs` | List payroll calendar runs |

### Benefits Module (4 tools)
| Tool | Description |
|------|-------------|
| `get_benefit_elections` | View benefit plan elections |
| `get_dependents` | Get dependent information |
| `get_beneficiaries` | Get beneficiary designations |
| `get_benefit_costs` | Calculate benefit costs |

### Performance Module (3 tools)
| Tool | Description |
|------|-------------|
| `get_performance_reviews` | List performance documents |
| `get_review_details` | Get detailed review information |
| `search_reviews` | Search reviews by criteria |

### PeopleTools Module (18 tools)
| Tool | Description |
|------|-------------|
| `get_record_definition` | Full record structure with fields and keys |
| `search_records` | Find records by name or description |
| `get_component_structure` | Component pages and navigation |
| `get_page_fields` | Fields on a page with record bindings |
| `get_peoplecode` | Find PeopleCode on records/fields |
| `get_permission_list_details` | Security access for permission lists |
| `get_roles_for_permission_list` | Roles containing a permission list |
| `get_process_definition` | Process Scheduler job definitions |
| `get_application_engine_steps` | AE program structure |
| `get_integration_broker_services` | IB service operations |
| `get_message_definition` | IB message structure |
| `get_query_definition` | PS Query records and fields |
| `get_sql_definition` | Get SQL text by SQLID (views, App Engine, PeopleCode) |
| `search_sql_definitions` | Search SQL objects by text |
| `search_peoplecode` | Search text within PeopleCode |
| `get_field_usage` | Impact analysis - where a field is used |
| `get_translate_field_values` | All XLAT values for a field |
| `explain_peoplesoft_concept` | Explains effective dating, SetID, etc. |

### Direct Query (1 tool)
| Tool | Description |
|------|-------------|
| `query_peoplesoft_db` | Execute custom SQL queries |

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| `peoplesoft://schema-guide` | Major tables by module |
| `peoplesoft://concepts` | Effective dating, EMPLID, SetID, XLAT |
| `peoplesoft://query-examples` | SQL query patterns |
| `peoplesoft://peopletools-guide` | PeopleTools architecture guide |

## Project Structure

```
peoplesoft-mcp/
├── peoplesoft_server.py    # Main MCP server entry point
├── db.py                   # Database connection management
├── tools/                  # Semantic tool modules
│   ├── introspection.py    # Schema discovery tools
│   ├── hr.py               # HR module tools
│   ├── payroll.py          # Payroll module tools
│   ├── benefits.py         # Benefits module tools
│   ├── performance.py      # ePerformance tools
│   └── peopletools.py      # PeopleTools metadata tools
├── tests/                  # Test suites
│   ├── test_business_questions.py   # HR business scenarios
│   └── test_peopletools_questions.py # Technical consultant scenarios
├── Reference_Documents/    # Documentation resources
│   ├── peoplesoft_concepts.md
│   ├── peoplesoft_schema_guide.md
│   ├── peopletools_guide.md
│   └── sql_query_examples.md
├── docs/
│   ├── peopletools-tables-by-tool.md   # Tables required per tool
│   └── migration-analysis.md   # Migration planning notes
└── pyproject.toml          # Project configuration
```

## Running Tests

```bash
# Set environment variables
export ORACLE_DSN="hostname:port/service_name"
export ORACLE_USER="username"
export ORACLE_PASSWORD="password"

# Run all tests
uv run pytest tests/ -v -s

# Run specific test suite
uv run pytest tests/test_business_questions.py -v -s
uv run pytest tests/test_peopletools_questions.py -v -s
```

## Example Queries

The MCP enables natural language questions like:

**Business Questions:**
- "How many active employees are in each company?"
- "What is the average salary by department?"
- "Who reports to manager X?"
- "Show me employees without a supervisor assigned"

**Technical Questions:**
- "What fields does PS_JOB have?"
- "Where is the DEPTID field used?"
- "What PeopleCode runs on the JOB record?"
- "What SQL does HR_ABSV_JOB_EFFDT use?"
- "Search for SQL objects referencing PS_ABSV_REQUEST"
- "Explain effective dating in PeopleSoft"

## Development

### Adding New Tools

1. Create a new module in `tools/` or add to existing module
2. Define async functions that use `db.execute_query()`
3. Add a `register_tools(mcp)` function
4. Import and register in `peoplesoft_server.py`

### Key Concepts

- **Effective Dating**: Most PeopleSoft tables use EFFDT/EFFSEQ for history
- **SetID**: Controls data sharing across business units
- **Translate Values**: Short codes decoded via PSXLATITEM
- **EMPLID/EMPL_RCD**: Employee ID + employment record number

## License

MIT

## Changelog

### v0.2.1 (2026-03-02)
- Added `get_sql_definition` - fetch SQL text by SQLID from PSSQLTEXTDEFN
- Added `search_sql_definitions` - search SQL objects by text
- PeopleTools compatibility: adjusted PSPNLGROUP, PSPNLFIELD, PSAEAPPLDEFN, PSAESTEPDEFN queries for varying column names across PeopleTools versions
- Added `docs/peopletools-tables-by-tool.md` - tables required per tool

### v0.2.0 (2026-02-28)
- Added modular tool architecture with 39 semantic tools
- Added PeopleTools introspection module (16 tools)
- Added comprehensive test suites (42 tests)
- Replaced connection pooling with direct connections for reliability
- Added 4 documentation resources
- Improved effective dating patterns in all queries

# Demolition Estimating

Desktop tooling for demolition estimating and financial analysis, 
built with Tkinter, PostgreSQL, pandas, scikit-learn, and Prophet.

## What This Repository Includes

This repo currently has two main GUI applications:

- Estimating + proposal workflow (`estimate_project/work_scope_bid_proposal.py`)
   - Multi-page work scope and bid proposal form
   - Contact and equipment lookup/edit windows
   - Historical + machine-learning estimate support
   - Word document export to your Downloads folder

- Financials workflow (`financials/financials_main.py`)
   - Daily/monthly/yearly operating-cost calculations
   - Equipment/disposal/sales/QuickBooks-style summaries
   - Forecast charts using Prophet (matplotlib and Plotly)

## Current Project Structure

```text
demolition_estimating/
├── data/
│   ├── equipment_sample_data_(2026-08-01).csv
│   ├── monthly_numbers_sample_data_(2026-08-01).csv
│   └── project_sample_data_(2026-08-01).csv
├── estimate_project/
│   ├── building_demo.py
│   ├── contact_book.py
│   ├── equipment_book.py
│   ├── estimate_project.py
│   ├── estimating_main.py
│   ├── house_demo.py
│   ├── interior_demo.py
│   ├── postgresql.py
│   └── work_scope_bid_proposal.py
├── financials/
│   ├── expenses.py
│   ├── financials_main.py
│   ├── postgresql.py
│   └── revenue.py
├── json_files/
│   ├── contacts.json
│   └── equipment.json
├── requirements.txt
├── README.md
└── LICENSE.txt
```

## Prerequisites

- Python 3.10+
- PostgreSQL database with required tables
- Tkinter (usually included with standard Python installers)

## Setup

1. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the repository root.

```env
POSTGRESQL_HOST=host
POSTGRESQL_PORT=port
DATABASE=your_database_name
POSTGRESQL_USER=your_username
POSTGRESQL_PASSWORD=your_password
```

Both `estimate_project/postgresql.py` and `financials/postgresql.py` read these same environment variables.

## Database Data Requirements

The application expects these tables:

- `project`
   - Used by estimating workflows
   - Columns used in code: `job_number`, `awarded_date`, `project_description`, 
   `structure_type`, `sqft`, `bid_price`, `job_cost`, `estimator`

- `monthly_numbers`
   - Used by financials workflows
   - Columns used in code: `year_month`, `disposalcost`, `expense`, `sales`, `payroll`

- `equipment`
   - Used by both financials and estimating workflows
   - Columns used in code: `equipment_name`, `project_type`, `purchase_price`, 
   `day_rate`, `week_rate`, `month_rate`

- `company` and `client`
   - Used by the contact book workflow

Sample CSVs in the `data/` directory show expected shape and naming.

## Running The Apps

From the repository root:

Main estimating/proposal GUI:

```bash
python estimate_project/work_scope_bid_proposal.py
```

Financials GUI:

```bash
python financials/financials_main.py
```

Optional standalone tools:

```bash
python estimate_project/contact_book.py
python estimate_project/equipment_book.py
python estimate_project/estimating_main.py
```

## Output

- Proposal documents are exported as `.docx` files to your user Downloads directory.
- Chart windows open via matplotlib and Plotly from within the desktop apps.

## Notes

- The `json_files/` directory remains in the repo, but core contact/equipment 
  workflows are currently PostgreSQL-backed.
- If your data queries return no rows, UI warnings may appear and model/chart 
  features will not run until data is present.

## License

This project is licensed under the MIT License. See `LICENSE.txt`.
# Demolition Estimating

## Overview

Demolition Estimating is a modular application for managing and estimating demolition 
projects. It features a GUI built with Tkinter, allowing users to input project details, 
select equipment, manage contacts, track financials, and generate bid proposals. 
The project is organized into several subdirectories for equipment management, 
project estimation, and financial tracking.

## Features

- Project overview and detailed input
- Methodology and order of operations documentation
- Alternates, inclusions, and exclusions management
- Equipment selection and cost calculation
- Contact management
- Financial dashboards (budgets, AR, etc.)
- Export bid proposals to Word documents

## Directory Structure

```
demolition_estimating/
│
├── equipment/
│   ├── equipment_cost.py
│   ├── equipment_dict.py
│   └── ...
│
├── estimate_project/
│   ├── work_scope_bid_proposal.py
│   ├── contact_book.py
│   ├── equipment_book.py
│   └── ...
│
├── financials/
│   ├── dashboards.py
│   ├── estimating_main.py
│   ├── financials_main.py
│   └── ...
│
├── json_files/
│   ├── contacts.json
│   ├── equipment.json
│   └── ...
│
├── .venv/
│   └── ...
│
├── requirements.txt
├── README.md
└── ...
```

## Getting Started

1. **Install dependencies**  
   Activate your virtual environment and install required packages:
   ```
   pip install -r requirements.txt
   ```

2. **Run the application**  
   Launch the main GUI:
   ```
   python estimate_project/work_scope_bid_proposal.py
   ```

3. **Add your data**  
   - Update `contacts.json` and `equipment.json` in the `json_files` directory 
   with your project-specific information.

## Usage

- Use the GUI to navigate through project estimation steps.
- Select equipment and calculate total costs.
- Access financial dashboards for budgets and accounts receivable.
- Export bid proposals as Word documents.

## Requirements

- Python 3.8+
- Tkinter
- tkcalendar
- python-docx
- python-dotenv

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please contact the project maintainer.
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import csv
import importlib
import importlib.util
import json
import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import uuid

if importlib.util.find_spec("openpyxl") is not None:
    _openpyxl = importlib.import_module("openpyxl")
    Workbook = _openpyxl.Workbook
    load_workbook = _openpyxl.load_workbook
else:
    Workbook = None
    load_workbook = None

if importlib.util.find_spec("tkcalendar") is not None:
    _tkcalendar = importlib.import_module("tkcalendar")
    DateEntry = _tkcalendar.DateEntry
else:
    DateEntry = None

if importlib.util.find_spec("matplotlib") is not None:
    _matplotlib = importlib.import_module("matplotlib")
    _matplotlib.use("TkAgg")
    plt = importlib.import_module("matplotlib.pyplot")
else:
    plt = None

if importlib.util.find_spec("mplcursors") is not None:
    mplcursors = importlib.import_module("mplcursors")
else:
    mplcursors = None

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

DATE_FMT = "%Y-%m-%d"
TRACK_STATUSES = ("Won", "Lost", "Bidding")
PROJECT_TYPE_OPTIONS = ("Interior Demolition", "House Demo", "Building Demo")
ESTIMATOR_OPTIONS = ("Estimator One", "Estimator Two", "Estimator Three", "Estimator Four")
COST_CODE_OPTIONS = ("0100", "0200", "0300", "0400")
COST_CODE_TO_DESCRIPTION = {
    "0100": "Labor",
    "0200": "Misc",
    "0300": "Equipment",
    "0400": "Disposal",
}
DEFAULT_CHART_START_DATE = "2024-01-01"
DEFAULT_CHART_END_DATE = "2026-12-31"


def safe_float(value: str, field_name: str) -> float:
    """Convert user text to float and raise a clear ValueError on invalid input."""
    text = (value or "").strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc


def safe_int(value: str, field_name: str) -> int:
    """Convert user text to integer and raise a clear ValueError on invalid input."""
    text = (value or "").strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid whole number.") from exc


def parse_date(value: str, field_name: str) -> date:
    """Parse a YYYY-MM-DD string into a date with user-friendly validation."""
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    try:
        return datetime.strptime(text, DATE_FMT).date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format.") from exc


def format_currency(value: float) -> str:
    """Format numeric value as currency for table presentation."""
    return f"${value:,.2f}"


def calculate_days_onsite(start_date: str, end_date: str) -> int:
    """Calculate days onsite as the difference between end date and start date."""
    try:
        start = parse_date(start_date, "Start Date")
        end = parse_date(end_date, "End Date")
    except ValueError:
        return 0
    return max((end - start).days, 0)


def calculate_duration_days(start_date: str, end_date: str) -> int:
    """Calculate inclusive duration from start date through end date."""
    try:
        start = parse_date(start_date, "Start Date")
        end = parse_date(end_date, "End Date")
    except ValueError:
        return 0
    return max((end - start).days + 1, 0)


class ProjectManagementApp:
    """Tkinter application for project management, scheduling, reporting, gantt, and map views."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize state, load data, build UI, and render initial views."""
        self.root = root
        self.root.title("Project Management")
        self.root.geometry("1360x800")
        self.root.minsize(1200, 700)

        self.data_directory, self.data_visibility = self._resolve_data_directory()
        self.data_file = os.path.join(
            self.data_directory,
            f"project_management_{self.data_visibility.lower()}.json",
        )

        self.data: dict[str, list[dict[str, object]]] = {"projects": [], "tasks": []}
        self.selected_project_id: str | None = None
        self.selected_task_id: str | None = None
        self.task_row_lookup: dict[str, str] = {}
        self.report_rows: list[dict[str, object]] = []
        self.gantt_rows: list[dict[str, object]] = []

        self.active_only_var = tk.BooleanVar(value=True)
        self.chart_status_filter_var = tk.StringVar(value="All Statuses")

        self.load_data()
        self.build_ui()
        self._safe_execute(self.refresh_all_views, title="Startup Error")
        self._safe_execute(self.clear_project_form, title="Startup Error")

    def _resolve_data_directory(self) -> tuple[str, str]:
        """Choose private json_files directory when available; otherwise use public data directory."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(base_dir)
        private_dir = os.path.join(base_dir, "json_files")
        public_dir = os.path.join(repo_root, "data")
        if os.path.isdir(private_dir):
            return private_dir, "PRIVATE"
        os.makedirs(public_dir, exist_ok=True)
        return public_dir, "PUBLIC"

    def _safe_execute(self, action, *, title: str = "Operation Failed") -> None:
        """Run a callback with centralized exception handling and user-safe messaging."""
        try:
            action()
        except ValueError as exc:
            LOGGER.warning("Validation failure during %s: %s", getattr(action, "__name__", "action"), exc)
            messagebox.showwarning("Validation Error", str(exc))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.exception("Data access failure during %s: %s", getattr(action, "__name__", "action"), exc)
            messagebox.showerror(title, "A data access error occurred. Please try again.")
        except Exception as exc:
            LOGGER.exception("Unexpected failure during %s: %s", getattr(action, "__name__", "action"), exc)
            messagebox.showerror(title, "An unexpected error occurred. Please try again.")

    def _get_date_value(self, widget) -> str:
        """Return normalized YYYY-MM-DD value from a date widget."""
        if hasattr(widget, "_optional_empty") and getattr(widget, "_optional_empty"):
            return ""
        if DateEntry is not None and isinstance(widget, DateEntry):
            return widget.get_date().isoformat()
        return widget.get().strip()

    def _set_date_value(self, widget, value: str) -> None:
        """Set a date widget to a YYYY-MM-DD value."""
        if hasattr(widget, "_optional_empty"):
            widget._optional_empty = not bool((value or "").strip())
            if widget._optional_empty:
                if DateEntry is not None and isinstance(widget, DateEntry):
                    widget.set_date(date.today())
                else:
                    widget.delete(0, tk.END)
                return
        if DateEntry is not None and isinstance(widget, DateEntry):
            widget.set_date(parse_date(value, "Date"))
            return
        widget.delete(0, tk.END)
        widget.insert(0, value)

    def _project_status_from_tasks(self, tasks: list[dict[str, object]]) -> str:
        """Calculate an aggregate project status from task statuses."""
        statuses = {str(task.get("status", "")).strip() for task in tasks if str(task.get("status", "")).strip()}
        if not statuses:
            return "Not Scheduled"
        if "Bidding" in statuses:
            return "Bidding"
        if "Won" in statuses:
            return "Won"
        if "Lost" in statuses:
            return "Lost"
        return sorted(statuses)[0]

    def _suggest_next_bid_number(self) -> str:
        """Return next available bid number in YYYY-0001 format for the current year."""
        current_year = datetime.now().year
        bid_counter_values: list[int] = []
        for project in self.data["projects"]:
            bid_number = str(project.get("bid_number", "")).strip()
            if not bid_number:
                continue
            if "-" not in bid_number:
                continue
            year_text, counter_text = bid_number.split("-", 1)
            if year_text.isdigit() and counter_text.isdigit() and int(year_text) == current_year:
                bid_counter_values.append(int(counter_text))
        next_counter = (max(bid_counter_values) + 1) if bid_counter_values else 1
        return f"{current_year}-{next_counter:04d}"

    def _calculate_pl_percent(self, bid_price: float, job_cost: float) -> float:
        """Return P&L percent based on bid and cost values."""
        if bid_price <= 0:
            return 0.0
        return round(((bid_price - job_cost) / bid_price) * 100, 2)

    def _normalize_project_record(self, project: dict[str, object]) -> dict[str, object]:
        """Normalize legacy/new project fields into current schema."""
        bid_number = str(project.get("bid_number") or project.get("job_number") or "").strip()
        if not bid_number:
            bid_number = self._suggest_next_bid_number()
        estimator = str(project.get("estimator") or project.get("project_manager") or "").strip()
        project_sqft = str(project.get("project_sqft") or project.get("crew_name") or "").strip()
        bid_price = float(project.get("bid_price", 0.0) or 0.0)
        job_cost = float(project.get("job_cost", 0.0) or 0.0)
        p_and_l = float(project.get("p_and_l", bid_price - job_cost) or (bid_price - job_cost))
        return {
            "id": str(project.get("id") or uuid.uuid4()),
            "project_type": str(project.get("project_type", "")).strip(),
            "project_address": str(project.get("project_address", "")).strip(),
            "bid_number": bid_number,
            "estimator": estimator,
            "project_sqft": project_sqft,
            "duration_days": int(project.get("duration_days", 0) or 0),
            "bid_price": bid_price,
            "job_cost": job_cost,
            "p_and_l": p_and_l,
            "p_and_l_percent": self._calculate_pl_percent(bid_price, job_cost),
        }

    def _normalize_task_record(self, task: dict[str, object]) -> dict[str, object]:
        """Normalize legacy/new task fields into current schema."""
        cost_code = str(task.get("cost_code") or task.get("task") or "").strip()
        if cost_code not in COST_CODE_OPTIONS:
            cost_code = "0100"
        cost_code_value = float(task.get("cost_code_value", 0.0) or 0.0)
        return {
            "id": str(task.get("id") or uuid.uuid4()),
            "cost_code": cost_code,
            "description": COST_CODE_TO_DESCRIPTION[cost_code],
            "cost_code_value": max(cost_code_value, 0.0),
            "bid_number": str(task.get("bid_number") or task.get("job_number") or "").strip(),
            "start_date": str(task.get("start_date", "")).strip(),
            "end_date": str(task.get("end_date", "")).strip(),
            "status": str(task.get("status") or "Bidding").strip() if str(task.get("status") or "Bidding").strip() in TRACK_STATUSES else "Bidding",
        }

    def _seed_public_sample_data(self) -> None:
        """Seed public sample data when no records exist."""
        if self.data_visibility != "PUBLIC":
            return
        if self.data["projects"] or self.data["tasks"]:
            return
        self.data["projects"] = [
            {
                "id": str(uuid.uuid4()),
                "project_type": "Interior Demolition",
                "project_address": "1200 Hamilton Ave, Phoenix, AZ",
                "bid_number": "2026-0001",
                "estimator": "Estimator One",
                "project_sqft": "12500",
                "duration_days": 18,
                "bid_price": 320000.0,
                "job_cost": 249500.0,
                "p_and_l": 70500.0,
                "p_and_l_percent": self._calculate_pl_percent(320000.0, 249500.0),
            },
            {
                "id": str(uuid.uuid4()),
                "project_type": "Building Demo",
                "project_address": "300 Foundry Rd, Birmingham, AL",
                "bid_number": "2026-0002",
                "estimator": "Estimator Two",
                "project_sqft": "28500",
                "duration_days": 25,
                "bid_price": 685000.0,
                "job_cost": 521250.0,
                "p_and_l": 163750.0,
                "p_and_l_percent": self._calculate_pl_percent(685000.0, 521250.0),
            },
        ]
        self.data["tasks"] = [
            {
                "id": str(uuid.uuid4()),
                "cost_code": "0100",
                "description": "Labor",
                "cost_code_value": 1800.0,
                "bid_number": "2026-0001",
                "start_date": "2026-01-08",
                "end_date": "2026-01-20",
                "status": "Bidding",
            },
            {
                "id": str(uuid.uuid4()),
                "cost_code": "0300",
                "description": "Equipment",
                "cost_code_value": 4200.0,
                "bid_number": "2026-0001",
                "start_date": "2026-01-10",
                "end_date": "2026-01-19",
                "status": "Won",
            },
            {
                "id": str(uuid.uuid4()),
                "cost_code": "0400",
                "description": "Disposal",
                "cost_code_value": 5300.0,
                "bid_number": "2026-0002",
                "start_date": "2026-02-03",
                "end_date": "2026-02-21",
                "status": "Bidding",
            },
        ]
        self.save_data()

    def load_data(self) -> None:
        """Load project and task JSON data from the selected repository data file."""
        if not os.path.exists(self.data_file):
            self.save_data()
            self._seed_public_sample_data()
            return
        with open(self.data_file, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        projects = loaded.get("projects", [])
        tasks = loaded.get("tasks", [])
        if not isinstance(projects, list) or not isinstance(tasks, list):
            raise ValueError("Data file structure is invalid.")
        self.data = {
            "projects": [self._normalize_project_record(project) for project in projects if isinstance(project, dict)],
            "tasks": [self._normalize_task_record(task) for task in tasks if isinstance(task, dict)],
        }
        self.save_data()

    def save_data(self) -> None:
        """Persist in-memory project and task data to JSON."""
        os.makedirs(self.data_directory, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)

    def build_ui(self) -> None:
        """Build notebook tabs and all tab-specific controls."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_projects = ttk.Frame(self.notebook)
        self.tab_tracking = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)
        self.tab_gantt = ttk.Frame(self.notebook)
        self.tab_map = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_projects, text="📕Estimating Project Management")
        self.notebook.add(self.tab_tracking, text="📍Track Bid")
        self.notebook.add(self.tab_reports, text="📄Reports")
        self.notebook.add(self.tab_gantt, text="📈Charts")
        self.notebook.add(self.tab_map, text="🗺️Map")

        self.build_project_management_tab()
        self.build_track_project_tab()
        self.build_reports_tab()
        self.build_gantt_tab()
        self.build_map_tab()

    def build_project_management_tab(self) -> None:
        """Build Project Management tab form, actions, and table."""
        form = ttk.LabelFrame(
            self.tab_projects,
            text=f"Estimating Project Management ({self.data_visibility} data file: {os.path.basename(self.data_file)})",
        )
        form.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        labels = (
            "Project Type",
            "Project Address",
            "Bid Number",
            "Estimator",
            "Project SqFt",
            "Duration (Days)",
            "Bid Price",
            "Job Cost",
            "P & L",
            "P & L %",
        )
        self.project_entries: dict[str, tk.Widget] = {}
        combo_defaults = {
            "Project Type": PROJECT_TYPE_OPTIONS,
            "Estimator": ESTIMATOR_OPTIONS,
        }
        for idx, label in enumerate(labels):
            col = (idx % 3) * 2
            row = idx // 3
            ttk.Label(form, text=label).grid(row=row, column=col, sticky="e", padx=6, pady=6)
            if label in combo_defaults:
                entry = ttk.Combobox(form, state="normal", width=33, values=combo_defaults[label])
            else:
                entry = ttk.Entry(form, width=36)
            entry.grid(row=row, column=col + 1, sticky="w", padx=6, pady=6)
            if label in {"P & L", "P & L %"}:
                entry.configure(state="readonly")
            self.project_entries[label] = entry

        self.project_entries["Bid Price"].bind("<KeyRelease>", lambda _: self.update_project_pl_preview())
        self.project_entries["Job Cost"].bind("<KeyRelease>", lambda _: self.update_project_pl_preview())

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=6, sticky="w", padx=6, pady=(4, 8))
        ttk.Button(buttons, text="Add Project", command=lambda: self._safe_execute(self.add_project)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Update Project", command=lambda: self._safe_execute(self.update_project)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Remove Project", command=lambda: self._safe_execute(self.remove_project)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Search Project", command=lambda: self._safe_execute(self.search_project)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear Results", command=lambda: self._safe_execute(self.clear_project_results)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Export", command=lambda: self._safe_execute(self.export_projects)).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.tab_projects, text="Projects")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)

        columns = (
            "project_type",
            "project_address",
            "bid_number",
            "estimator",
            "project_sqft",
            "duration_days",
            "bid_price",
            "job_cost",
            "p_and_l",
            "p_and_l_percent",
        )
        self.project_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        headings = (
            "Project Type",
            "Project Address",
            "Bid Number",
            "Estimator",
            "Project SqFt",
            "Duration (Days)",
            "Bid Price",
            "Job Cost",
            "P & L",
            "P & L %",
        )
        for col, text in zip(columns, headings):
            self.project_tree.heading(col, text=text)
            width = 140 if col not in {"project_address", "estimator"} else 210
            self.project_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scroll.set)
        self.project_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.project_tree.bind("<<TreeviewSelect>>", self.on_project_selected)

        self.tab_projects.rowconfigure(1, weight=1)
        self.tab_projects.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def build_track_project_tab(self) -> None:
        """Build Track Bid tab controls and grouped task table."""
        form = ttk.LabelFrame(self.tab_tracking, text="Task Assignment")
        form.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        ttk.Label(form, text="Cost Code").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.cost_code_combo = ttk.Combobox(form, state="readonly", width=34, values=COST_CODE_OPTIONS)
        self.cost_code_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        self.cost_code_combo.bind("<<ComboboxSelected>>", self.on_cost_code_selected)
        self.cost_code_combo.set(COST_CODE_OPTIONS[0])

        ttk.Label(form, text="Description").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.description_entry = ttk.Entry(form, width=44)
        self.description_entry.grid(row=0, column=3, sticky="w", padx=6, pady=6)
        self.description_entry.insert(0, COST_CODE_TO_DESCRIPTION[COST_CODE_OPTIONS[0]])
        self.description_entry.configure(state="readonly")

        ttk.Label(form, text="Cost Code Value").grid(row=1, column=2, sticky="e", padx=6, pady=6)
        self.cost_code_value_entry = ttk.Entry(form, width=22)
        self.cost_code_value_entry.grid(row=1, column=3, sticky="w", padx=6, pady=6)
        self.cost_code_value_entry.insert(0, "0")

        ttk.Label(form, text="Bid Number").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.task_bid_combo = ttk.Combobox(form, state="normal", width=32)
        self.task_bid_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Start Date (Optional)").grid(row=2, column=2, sticky="e", padx=6, pady=6)
        if DateEntry is not None:
            self.start_date_entry = DateEntry(form, width=19, date_pattern="yyyy-mm-dd")
        else:
            self.start_date_entry = ttk.Entry(form, width=22)
        self.start_date_entry.grid(row=2, column=3, sticky="w", padx=6, pady=6)
        self.start_date_entry._optional_empty = True
        if DateEntry is not None:
            self.start_date_entry.bind("<<DateEntrySelected>>", lambda _e: self.on_optional_date_selected(self.start_date_entry))
        else:
            self.start_date_entry.bind("<KeyRelease>", lambda _e: self.on_optional_date_selected(self.start_date_entry))
        self._set_date_value(self.start_date_entry, "")

        ttk.Label(form, text="End Date (Optional)").grid(row=3, column=2, sticky="e", padx=6, pady=6)
        if DateEntry is not None:
            self.end_date_entry = DateEntry(form, width=19, date_pattern="yyyy-mm-dd")
        else:
            self.end_date_entry = ttk.Entry(form, width=22)
        self.end_date_entry.grid(row=3, column=3, sticky="w", padx=6, pady=6)
        self.end_date_entry._optional_empty = True
        if DateEntry is not None:
            self.end_date_entry.bind("<<DateEntrySelected>>", lambda _e: self.on_optional_date_selected(self.end_date_entry))
        else:
            self.end_date_entry.bind("<KeyRelease>", lambda _e: self.on_optional_date_selected(self.end_date_entry))
        self._set_date_value(self.end_date_entry, "")

        ttk.Label(form, text="Status").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.status_combo = ttk.Combobox(form, state="readonly", width=32, values=TRACK_STATUSES)
        self.status_combo.grid(row=3, column=1, sticky="w", padx=6, pady=6)
        self.status_combo.set("Bidding")

        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=0, columnspan=4, sticky="w", padx=6, pady=(4, 8))
        ttk.Button(buttons, text="Assign Cost Code", command=lambda: self._safe_execute(self.assign_task)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Refresh", command=lambda: self._safe_execute(self.refresh_task_tree)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear", command=lambda: self._safe_execute(self.clear_task_form)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Edit", command=lambda: self._safe_execute(self.edit_selected_task)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Import", command=lambda: self._safe_execute(self.import_tasks)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Export", command=lambda: self._safe_execute(self.export_tasks)).pack(side="left", padx=5)
        ttk.Button(buttons, text="Template", command=lambda: self._safe_execute(self.save_task_template)).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.tab_tracking, text="Bid Cost Codes Grouped by Bid Number and Project Address")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        columns = ("cost_code", "description", "cost_code_value", "start_date", "end_date", "duration", "status")
        self.task_tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", height=15)
        self.task_tree.heading("#0", text="Group")
        self.task_tree.column("#0", width=340, anchor="w")
        headings = ("Cost Code", "Description", "Cost Code Value", "Start Date", "End Date", "Duration (Days)", "Status")
        widths = (120, 180, 130, 120, 120, 120, 120)
        for col, text, width in zip(columns, headings, widths):
            self.task_tree.heading(col, text=text)
            self.task_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scroll.set)
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_selected)

        self.tab_tracking.rowconfigure(1, weight=1)
        self.tab_tracking.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def build_reports_tab(self) -> None:
        """Build Reports tab filters, actions, results tree, and summary pane."""
        filter_frame = ttk.LabelFrame(self.tab_reports, text="Report Filters")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        ttk.Label(filter_frame, text="Bid Number").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.report_bid_combo = ttk.Combobox(filter_frame, state="normal", width=24)
        self.report_bid_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(filter_frame, text="Address").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.report_address_combo = ttk.Combobox(filter_frame, state="normal", width=38)
        self.report_address_combo.grid(row=0, column=3, sticky="w", padx=6, pady=6)

        ttk.Label(filter_frame, text="Project Type").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.report_project_type_combo = ttk.Combobox(filter_frame, state="normal", width=24)
        self.report_project_type_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(filter_frame, text="Estimator").grid(row=1, column=2, sticky="e", padx=6, pady=6)
        self.report_estimator_combo = ttk.Combobox(filter_frame, state="normal", width=38)
        self.report_estimator_combo.grid(row=1, column=3, sticky="w", padx=6, pady=6)

        ttk.Checkbutton(filter_frame, text="Active Only", variable=self.active_only_var).grid(
            row=0,
            column=4,
            sticky="w",
            padx=6,
            pady=6,
        )

        actions = ttk.Frame(filter_frame)
        actions.grid(row=2, column=0, columnspan=5, sticky="w", padx=6, pady=(2, 8))
        ttk.Button(actions, text="Run Filtered Report", command=lambda: self._safe_execute(self.run_filtered_report)).pack(side="left", padx=5)
        ttk.Button(actions, text="All Active Projects", command=lambda: self._safe_execute(self.show_all_active_projects)).pack(side="left", padx=5)
        ttk.Button(actions, text="Project History", command=lambda: self._safe_execute(self.show_project_history)).pack(side="left", padx=5)
        ttk.Button(actions, text="Clear", command=lambda: self._safe_execute(self.clear_report_filters)).pack(side="left", padx=5)
        ttk.Button(actions, text="Export", command=lambda: self._safe_execute(self.export_reports)).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.tab_reports, text="Report Results")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        columns = (
            "bid_number",
            "project_address",
            "project_type",
            "estimator",
            "start_date",
            "end_date",
            "duration_days",
            "status",
            "bid_price",
            "job_cost",
            "p_and_l",
            "p_and_l_percent",
        )
        self.report_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        headings = (
            "Bid Number",
            "Project Address",
            "Project Type",
            "Estimator",
            "Start Date",
            "End Date",
            "Duration (Days)",
            "Status",
            "Bid Price",
            "Job Cost",
            "P & L",
            "P & L %",
        )
        widths = (120, 260, 150, 130, 110, 110, 120, 110, 110, 110, 110, 90)
        for col, text, width in zip(columns, headings, widths):
            self.report_tree.heading(col, text=text)
            self.report_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scroll.set)
        self.report_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        summary_frame = ttk.LabelFrame(self.tab_reports, text="Summary View")
        summary_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=9, wrap=tk.WORD)
        self.summary_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.summary_text.configure(state="disabled")

        self.tab_reports.rowconfigure(1, weight=1)
        self.tab_reports.rowconfigure(2, weight=1)
        self.tab_reports.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        summary_frame.columnconfigure(0, weight=1)

    def build_gantt_tab(self) -> None:
        """Build Charts tab controls, chart canvas, and chart details tree."""
        controls = ttk.LabelFrame(self.tab_gantt, text="Chart Controls")
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        filter_fields = ttk.Frame(controls)
        filter_fields.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))

        ttk.Label(filter_fields, text="Project Type").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.chart_project_type_combo = ttk.Combobox(
            filter_fields,
            state="normal",
            width=22,
            values=PROJECT_TYPE_OPTIONS,
        )
        self.chart_project_type_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(filter_fields, text="Approx SqFt").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.chart_sqft_entry = ttk.Entry(filter_fields, width=16)
        self.chart_sqft_entry.grid(row=0, column=3, sticky="w", padx=6, pady=6)

        ttk.Label(filter_fields, text="Estimator").grid(row=0, column=4, sticky="e", padx=6, pady=6)
        self.chart_estimator_combo = ttk.Combobox(filter_fields, state="normal", width=22)
        self.chart_estimator_combo.grid(row=0, column=5, sticky="w", padx=6, pady=6)

        ttk.Label(filter_fields, text="Status").grid(row=0, column=6, sticky="e", padx=6, pady=6)
        self.chart_status_combo = ttk.Combobox(
            filter_fields,
            state="readonly",
            width=18,
            textvariable=self.chart_status_filter_var,
            values=("All Statuses",) + TRACK_STATUSES,
        )
        self.chart_status_combo.grid(row=0, column=7, sticky="w", padx=6, pady=6)
        self.chart_status_combo.set("All Statuses")

        ttk.Label(filter_fields, text="Chart Option").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.chart_option_combo = ttk.Combobox(
            filter_fields,
            state="readonly",
            width=18,
            values=("Project", "Estimator", "Status"),
        )
        self.chart_option_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        self.chart_option_combo.set("Project")

        ttk.Label(filter_fields, text="Start Date").grid(row=1, column=2, sticky="e", padx=6, pady=6)
        if DateEntry is not None:
            self.gantt_start_filter = DateEntry(filter_fields, width=14, date_pattern="yyyy-mm-dd")
            self.gantt_start_filter.set_date(parse_date(DEFAULT_CHART_START_DATE, "Chart Start Date"))
        else:
            self.gantt_start_filter = ttk.Entry(filter_fields, width=17)
            self.gantt_start_filter.insert(0, DEFAULT_CHART_START_DATE)
        self.gantt_start_filter.grid(row=1, column=3, sticky="w", padx=6, pady=6)

        ttk.Label(filter_fields, text="End Date").grid(row=1, column=4, sticky="e", padx=6, pady=6)
        if DateEntry is not None:
            self.gantt_end_filter = DateEntry(filter_fields, width=14, date_pattern="yyyy-mm-dd")
            self.gantt_end_filter.set_date(parse_date(DEFAULT_CHART_END_DATE, "Chart End Date"))
        else:
            self.gantt_end_filter = ttk.Entry(filter_fields, width=17)
            self.gantt_end_filter.insert(0, DEFAULT_CHART_END_DATE)
        self.gantt_end_filter.grid(row=1, column=5, sticky="w", padx=6, pady=6)
        filter_fields.columnconfigure(8, weight=1)

        button_row = ttk.Frame(controls)
        button_row.grid(row=1, column=0, sticky="ew", padx=6, pady=(2, 6))
        ttk.Button(button_row, text="Search", command=lambda: self._safe_execute(self.refresh_gantt)).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=4,
        )
        ttk.Button(button_row, text="Display Chart", command=lambda: self._safe_execute(self.display_chart)).grid(
            row=0,
            column=1,
            sticky="w",
            padx=6,
            pady=4,
        )
        ttk.Button(button_row, text="Clear", command=lambda: self._safe_execute(self.clear_chart_filters)).grid(
            row=0,
            column=2,
            sticky="w",
            padx=6,
            pady=4,
        )
        button_row.columnconfigure(3, weight=1)
        controls.columnconfigure(0, weight=1)

        chart_frame = ttk.LabelFrame(self.tab_gantt, text="Chart Preview")
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self.gantt_canvas = tk.Canvas(chart_frame, background="#ffffff", height=320, highlightthickness=1, highlightbackground="#cccccc")
        self.gantt_canvas.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        details_frame = ttk.LabelFrame(self.tab_gantt, text="Chart Details")
        details_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        columns = (
            "bid_number",
            "address",
            "project_type",
            "estimator",
            "project_sqft",
            "duration_days",
            "bid_price",
            "job_cost",
            "p_and_l",
            "p_and_l_percent",
        )
        self.gantt_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=8)
        headings = ("Bid Number", "Address", "Project Type", "Estimator", "SqFt", "Duration (Days)", "Bid Price", "Job Cost", "P & L", "P & L %")
        widths = (120, 240, 160, 150, 90, 120, 120, 120, 120, 100)
        for col, text, width in zip(columns, headings, widths):
            self.gantt_tree.heading(col, text=text)
            self.gantt_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.gantt_tree.yview)
        self.gantt_tree.configure(yscrollcommand=scroll.set)
        self.gantt_tree.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scroll.grid(row=0, column=1, sticky="ns", pady=6)

        self.tab_gantt.rowconfigure(1, weight=1)
        self.tab_gantt.rowconfigure(2, weight=1)
        self.tab_gantt.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)

    def build_map_tab(self) -> None:
        """Build map-like visualization and active location list using task data."""
        controls = ttk.LabelFrame(self.tab_map, text="Map Controls")
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        ttk.Label(controls, text="Map View built from active project locations.").grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=6,
        )
        ttk.Button(controls, text="Refresh Map", command=lambda: self._safe_execute(self.refresh_map)).grid(
            row=0,
            column=1,
            sticky="e",
            padx=6,
            pady=6,
        )
        controls.columnconfigure(0, weight=1)

        map_frame = ttk.LabelFrame(self.tab_map, text="Map View")
        map_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self.map_canvas = tk.Canvas(
            map_frame,
            background="#f4f4f4",
            height=330,
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        self.map_canvas.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        active_frame = ttk.LabelFrame(self.tab_map, text="Active Location List")
        active_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        columns = ("marker", "bid_number", "project_address", "status")
        self.map_tree = ttk.Treeview(active_frame, columns=columns, show="headings", height=9)
        headings = ("Marker", "Bid Number", "Project Address", "Status")
        widths = (70, 120, 500, 140)
        for col, text, width in zip(columns, headings, widths):
            self.map_tree.heading(col, text=text)
            self.map_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(active_frame, orient="vertical", command=self.map_tree.yview)
        self.map_tree.configure(yscrollcommand=scroll.set)
        self.map_tree.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scroll.grid(row=0, column=1, sticky="ns", pady=6)

        self.tab_map.rowconfigure(1, weight=1)
        self.tab_map.rowconfigure(2, weight=1)
        self.tab_map.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        active_frame.rowconfigure(0, weight=1)
        active_frame.columnconfigure(0, weight=1)

    def refresh_all_views(self) -> None:
        """Refresh every dynamic control from current data."""
        self.refresh_project_tree()
        self.refresh_task_tree()
        self.refresh_report_filter_values()
        self.run_filtered_report()
        self.refresh_gantt()
        self.refresh_map()

    def _find_project_by_job(self, job_number: str) -> dict[str, object] | None:
        """Return project by bid number or None when no match exists."""
        for project in self.data["projects"]:
            if str(project.get("bid_number", "")).strip() == str(job_number).strip():
                return project
        return None

    def _find_project_by_id(self, project_id: str) -> dict[str, object] | None:
        """Return project by internal identifier or None if not found."""
        for project in self.data["projects"]:
            if str(project.get("id")) == project_id:
                return project
        return None

    def _find_task_by_id(self, task_id: str) -> dict[str, object] | None:
        """Return task by internal identifier or None if not found."""
        for task in self.data["tasks"]:
            if str(task.get("id")) == task_id:
                return task
        return None

    def _project_input(self) -> dict[str, object]:
        """Read, validate, and normalize project form values."""
        project_type = self.project_entries["Project Type"].get().strip()
        project_address = self.project_entries["Project Address"].get().strip()
        bid_number = self.project_entries["Bid Number"].get().strip()
        estimator = self.project_entries["Estimator"].get().strip()
        project_sqft = self.project_entries["Project SqFt"].get().strip()
        duration_days = safe_int(self.project_entries["Duration (Days)"].get(), "Duration (Days)")
        bid_price = safe_float(self.project_entries["Bid Price"].get(), "Bid Price")
        job_cost = safe_float(self.project_entries["Job Cost"].get(), "Job Cost")
        if duration_days < 0:
            raise ValueError("Duration (Days) cannot be negative.")
        if not all([project_type, project_address, bid_number, estimator]):
            raise ValueError("All project fields except P & L are required.")
        if "-" not in bid_number:
            raise ValueError("Bid Number must be in YYYY-0001 format.")
        year_text, counter_text = bid_number.split("-", 1)
        if not (year_text.isdigit() and len(year_text) == 4 and counter_text.isdigit() and len(counter_text) == 4):
            raise ValueError("Bid Number must be in YYYY-0001 format.")
        pl_value = bid_price - job_cost
        return {
            "project_type": project_type,
            "project_address": project_address,
            "bid_number": bid_number,
            "estimator": estimator,
            "project_sqft": project_sqft,
            "duration_days": duration_days,
            "bid_price": bid_price,
            "job_cost": job_cost,
            "p_and_l": pl_value,
            "p_and_l_percent": self._calculate_pl_percent(bid_price, job_cost),
        }

    def update_project_pl_preview(self) -> None:
        """Update read-only P & L preview value from Bid Price and Job Cost inputs."""
        try:
            bid_price = safe_float(self.project_entries["Bid Price"].get(), "Bid Price")
            job_cost = safe_float(self.project_entries["Job Cost"].get(), "Job Cost")
            profit_value = bid_price - job_cost
            value = format_currency(profit_value)
            percent_value = f"{self._calculate_pl_percent(bid_price, job_cost):.2f}%"
        except ValueError:
            value = ""
            percent_value = ""
        self.project_entries["P & L"].configure(state="normal")
        self.project_entries["P & L"].delete(0, tk.END)
        self.project_entries["P & L"].insert(0, value)
        self.project_entries["P & L"].configure(state="readonly")
        self.project_entries["P & L %"].configure(state="normal")
        self.project_entries["P & L %"].delete(0, tk.END)
        self.project_entries["P & L %"].insert(0, percent_value)
        self.project_entries["P & L %"].configure(state="readonly")

    def add_project(self) -> None:
        """Add a new project from form data."""
        payload = self._project_input()
        if self._find_project_by_job(str(payload["bid_number"])) is not None:
            raise ValueError("Bid Number already exists.")
        payload["id"] = str(uuid.uuid4())
        self.data["projects"].append(payload)
        self.save_data()
        self.refresh_all_views()
        self.clear_project_form()
        messagebox.showinfo("Success", "Project added.")

    def update_project(self) -> None:
        """Update selected project with current form values."""
        if not self.selected_project_id:
            raise ValueError("Select a project to update.")
        project = self._find_project_by_id(self.selected_project_id)
        if project is None:
            raise ValueError("Selected project was not found.")
        payload = self._project_input()
        existing = self._find_project_by_job(str(payload["bid_number"]))
        if existing is not None and str(existing.get("id")) != self.selected_project_id:
            raise ValueError("Bid Number already exists for another project.")
        for key, value in payload.items():
            project[key] = value
        self.save_data()
        self.refresh_all_views()
        messagebox.showinfo("Success", "Project updated.")

    def remove_project(self) -> None:
        """Remove selected project and linked tasks."""
        if not self.selected_project_id:
            raise ValueError("Select a project to remove.")
        project = self._find_project_by_id(self.selected_project_id)
        if project is None:
            raise ValueError("Selected project was not found.")
        if not messagebox.askyesno("Confirm Remove", "Remove selected project and linked tasks?"):
            return
        bid_number = str(project.get("bid_number", ""))
        self.data["projects"] = [p for p in self.data["projects"] if str(p.get("id")) != self.selected_project_id]
        self.data["tasks"] = [t for t in self.data["tasks"] if str(t.get("bid_number", "")).strip() != bid_number]
        self.selected_project_id = None
        self.save_data()
        self.refresh_all_views()
        self.clear_project_form()
        messagebox.showinfo("Success", "Project removed.")

    def search_project(self) -> None:
        """Filter project tree by non-empty form fields."""
        filters = {
            "project_type": self.project_entries["Project Type"].get().strip().lower(),
            "project_address": self.project_entries["Project Address"].get().strip().lower(),
            "bid_number": self.project_entries["Bid Number"].get().strip().lower(),
            "estimator": self.project_entries["Estimator"].get().strip().lower(),
            "project_sqft": self.project_entries["Project SqFt"].get().strip().lower(),
        }

        filtered = []
        for project in self.data["projects"]:
            match = True
            for key, expected in filters.items():
                if expected and expected not in str(project.get(key, "")).lower():
                    match = False
                    break
            if match:
                filtered.append(project)
        self.refresh_project_tree(filtered)

    def clear_project_results(self) -> None:
        """Clear project form and reset tree to all projects."""
        self.clear_project_form()
        self.refresh_project_tree()

    def clear_project_form(self) -> None:
        """Clear project entry fields and active selection state."""
        self.selected_project_id = None
        for entry in self.project_entries.values():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
        self.project_entries["Bid Number"].insert(0, self._suggest_next_bid_number())
        self.project_entries["P & L"].configure(state="readonly")
        self.project_entries["P & L %"].configure(state="readonly")

    def on_project_selected(self, _event) -> None:
        """Load selected project values into the form."""
        selected = self.project_tree.selection()
        if not selected:
            return
        project_id = selected[0]
        project = self._find_project_by_id(project_id)
        if project is None:
            return
        self.selected_project_id = project_id
        value_map = {
            "Project Type": project.get("project_type", ""),
            "Project Address": project.get("project_address", ""),
            "Bid Number": project.get("bid_number", ""),
            "Estimator": project.get("estimator", ""),
            "Project SqFt": project.get("project_sqft", ""),
            "Duration (Days)": project.get("duration_days", ""),
            "Bid Price": project.get("bid_price", 0.0),
            "Job Cost": project.get("job_cost", 0.0),
            "P & L": project.get("p_and_l", 0.0),
            "P & L %": project.get("p_and_l_percent", 0.0),
        }
        for label, entry in self.project_entries.items():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            value = value_map[label]
            if label in {"Bid Price", "Job Cost", "P & L"}:
                entry.insert(0, format_currency(float(value)).replace("$", ""))
            elif label == "P & L %":
                entry.insert(0, f"{float(value):.2f}%")
            else:
                entry.insert(0, str(value))
            if label in {"P & L", "P & L %"}:
                entry.configure(state="readonly")

    def refresh_project_tree(self, rows: list[dict[str, object]] | None = None) -> None:
        """Render provided project rows or all projects into the Project Management tree."""
        self.project_tree.delete(*self.project_tree.get_children())
        source = rows if rows is not None else self.data["projects"]
        for project in source:
            self.project_tree.insert(
                "",
                "end",
                iid=str(project.get("id")),
                values=(
                    project.get("project_type", ""),
                    project.get("project_address", ""),
                    project.get("bid_number", ""),
                    project.get("estimator", ""),
                    project.get("project_sqft", ""),
                    project.get("duration_days", 0),
                    format_currency(float(project.get("bid_price", 0.0))),
                    format_currency(float(project.get("job_cost", 0.0))),
                    format_currency(float(project.get("p_and_l", 0.0))),
                    f"{float(project.get('p_and_l_percent', 0.0)):.2f}%",
                ),
            )
        self._refresh_project_dropdown_values()
        self.refresh_report_filter_values()
        self.refresh_task_job_values()

    def _refresh_project_dropdown_values(self) -> None:
        """Update editable combobox option lists with starter and existing project values."""
        if not isinstance(self.project_entries.get("Project Type"), ttk.Combobox):
            return
        type_values = sorted(
            set(PROJECT_TYPE_OPTIONS).union(
                str(p.get("project_type", "")).strip() for p in self.data["projects"] if p.get("project_type")
            )
        )
        manager_values = sorted(
            set(ESTIMATOR_OPTIONS).union(
                str(p.get("estimator", "")).strip() for p in self.data["projects"] if p.get("estimator")
            )
        )
        self.project_entries["Project Type"]["values"] = type_values
        self.project_entries["Estimator"]["values"] = manager_values

    def export_projects(self) -> None:
        """Export project table to CSV or XLSX."""
        file_path = filedialog.asksaveasfilename(
            title="Export Projects",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        headers = [
            "Project Type",
            "Project Address",
            "Bid Number",
            "Estimator",
            "Project SqFt",
            "Duration (Days)",
            "Bid Price",
            "Job Cost",
            "P & L",
            "P & L %",
        ]
        rows = [
            [
                p.get("project_type", ""),
                p.get("project_address", ""),
                p.get("bid_number", ""),
                p.get("estimator", ""),
                p.get("project_sqft", ""),
                p.get("duration_days", 0),
                p.get("bid_price", 0.0),
                p.get("job_cost", 0.0),
                p.get("p_and_l", 0.0),
                p.get("p_and_l_percent", 0.0),
            ]
            for p in self.data["projects"]
        ]
        self._write_table(file_path, headers, rows)
        messagebox.showinfo("Export Complete", "Project export complete.")

    def refresh_task_job_values(self) -> None:
        """Populate bid number dropdown from existing projects."""
        bid_numbers = sorted({str(p.get("bid_number", "")).strip() for p in self.data["projects"] if p.get("bid_number")})
        self.task_bid_combo["values"] = bid_numbers

    def on_cost_code_selected(self, _event=None) -> None:
        """Set readonly description based on selected cost code."""
        cost_code = self.cost_code_combo.get().strip()
        description = COST_CODE_TO_DESCRIPTION.get(cost_code, "")
        self.description_entry.configure(state="normal")
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, description)
        self.description_entry.configure(state="readonly")

    def on_optional_date_selected(self, widget) -> None:
        """Mark optional date widget as explicitly selected."""
        if hasattr(widget, "_optional_empty"):
            widget._optional_empty = False

    def _task_input(self) -> dict[str, object]:
        """Read, validate, and normalize Track Bid form values."""
        cost_code = self.cost_code_combo.get().strip()
        description = COST_CODE_TO_DESCRIPTION.get(cost_code, "")
        cost_code_value = safe_float(self.cost_code_value_entry.get().strip(), "Cost Code Value")
        job_number = self.task_bid_combo.get().strip()
        start_date = self._get_date_value(self.start_date_entry)
        end_date = self._get_date_value(self.end_date_entry)
        status = self.status_combo.get().strip()
        if not all([cost_code, job_number, status]):
            raise ValueError("Cost Code, Bid Number, and Status are required.")
        if cost_code_value < 0:
            raise ValueError("Cost Code Value cannot be negative.")
        if cost_code not in COST_CODE_OPTIONS:
            raise ValueError("Cost Code must be one of the allowed options.")
        if status not in TRACK_STATUSES:
            raise ValueError("Status must be one of the allowed options.")
        if start_date and end_date:
            start_obj = parse_date(start_date, "Start Date")
            end_obj = parse_date(end_date, "End Date")
            if end_obj < start_obj:
                raise ValueError("End Date must be on or after Start Date.")
        elif start_date or end_date:
            raise ValueError("Start Date and End Date must both be provided when one is provided.")
        return {
            "cost_code": cost_code,
            "description": description,
            "cost_code_value": cost_code_value,
            "bid_number": job_number,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
        }

    def assign_task(self) -> None:
        """Create a task assignment for a project."""
        payload = self._task_input()
        if self._find_project_by_job(str(payload["bid_number"])) is None:
            raise ValueError("Bid Number does not exist in Project Management.")
        payload["id"] = str(uuid.uuid4())
        self.data["tasks"].append(payload)
        self.save_data()
        self.refresh_all_views()
        self.clear_task_form()
        messagebox.showinfo("Success", "Cost code assigned.")

    def clear_task_form(self) -> None:
        """Clear task form fields and reset default status."""
        self.selected_task_id = None
        self.cost_code_combo.set(COST_CODE_OPTIONS[0])
        self.on_cost_code_selected()
        self.cost_code_value_entry.delete(0, tk.END)
        self.cost_code_value_entry.insert(0, "0")
        self.task_bid_combo.set("")
        self._set_date_value(self.start_date_entry, "")
        self._set_date_value(self.end_date_entry, "")
        self.status_combo.set("Bidding")

    def on_task_selected(self, _event) -> None:
        """Populate task form when user selects a task child row."""
        selected = self.task_tree.selection()
        if not selected:
            return
        item_id = selected[0]
        task_id = self.task_row_lookup.get(item_id)
        if not task_id:
            return
        task = self._find_task_by_id(task_id)
        if task is None:
            return
        self.selected_task_id = task_id
        self.cost_code_combo.set(str(task.get("cost_code", COST_CODE_OPTIONS[0])))
        self.description_entry.configure(state="normal")
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, str(task.get("description", COST_CODE_TO_DESCRIPTION.get(self.cost_code_combo.get().strip(), ""))))
        self.description_entry.configure(state="readonly")
        self.cost_code_value_entry.delete(0, tk.END)
        self.cost_code_value_entry.insert(0, str(float(task.get("cost_code_value", 0.0) or 0.0)))
        self.task_bid_combo.set(str(task.get("bid_number", "")))
        self._set_date_value(self.start_date_entry, str(task.get("start_date", "")))
        self._set_date_value(self.end_date_entry, str(task.get("end_date", "")))
        self.status_combo.set(str(task.get("status", "Bidding")))

    def edit_selected_task(self) -> None:
        """Save edits from the task form to the selected task."""
        if not self.selected_task_id:
            raise ValueError("Select a task row to edit.")
        task = self._find_task_by_id(self.selected_task_id)
        if task is None:
            raise ValueError("Selected task was not found.")
        payload = self._task_input()
        if self._find_project_by_job(str(payload["bid_number"])) is None:
            raise ValueError("Bid Number does not exist in Project Management.")
        for key, value in payload.items():
            task[key] = value
        self.save_data()
        self.refresh_all_views()
        messagebox.showinfo("Success", "Task updated.")

    def refresh_task_tree(self) -> None:
        """Render grouped task tree by bid number and project address."""
        self.task_tree.delete(*self.task_tree.get_children())
        self.task_row_lookup.clear()
        grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
        for task in self.data["tasks"]:
            job_number = str(task.get("bid_number", "")).strip()
            project = self._find_project_by_job(job_number)
            address = str(project.get("project_address", "Unknown Address")) if project else "Unknown Address"
            grouped.setdefault((job_number, address), []).append(task)

        for (job_number, address), tasks in sorted(grouped.items(), key=lambda item: item[0][0]):
            parent_iid = f"group::{job_number}::{address}"
            label = f"{job_number} | {address}"
            group_start_dates: list[date] = []
            group_end_dates: list[date] = []
            for task in tasks:
                start_text = str(task.get("start_date", "")).strip()
                end_text = str(task.get("end_date", "")).strip()
                if not (start_text and end_text):
                    continue
                try:
                    group_start_dates.append(parse_date(start_text, "Start Date"))
                    group_end_dates.append(parse_date(end_text, "End Date"))
                except ValueError:
                    LOGGER.warning("Skipping invalid task dates in group view for task id=%s", task.get("id"))

            group_start = min(group_start_dates).isoformat() if group_start_dates else ""
            group_end = max(group_end_dates).isoformat() if group_end_dates else ""
            group_duration = calculate_duration_days(group_start, group_end) if (group_start and group_end) else 0
            group_status = self._project_status_from_tasks(tasks)
            grouped_cost_codes = ", ".join(sorted({str(task.get("cost_code", "")) for task in tasks if task.get("cost_code")}))
            group_cost_code_value = sum(float(task.get("cost_code_value", 0.0) or 0.0) for task in tasks)
            self.task_tree.insert(
                "",
                "end",
                iid=parent_iid,
                text=label,
                values=(
                    grouped_cost_codes,
                    "Cost Code Total",
                    format_currency(group_cost_code_value),
                    group_start,
                    group_end,
                    group_duration,
                    group_status,
                ),
            )
            for task in tasks:
                task_id = str(task.get("id"))
                row_iid = f"task::{task_id}"
                self.task_tree.insert(
                    parent_iid,
                    "end",
                    iid=row_iid,
                    text="",
                    values=(
                        task.get("cost_code", ""),
                        task.get("description", ""),
                        format_currency(float(task.get("cost_code_value", 0.0) or 0.0)),
                        "",
                        "",
                        "",
                        "",
                    ),
                )
                self.task_row_lookup[row_iid] = task_id
            self.task_tree.item(parent_iid, open=True)

    def import_tasks(self) -> None:
        """Import tasks from CSV or XLSX."""
        file_path = filedialog.askopenfilename(
            title="Import Tasks",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        rows = self._read_table(file_path)
        required = {"Cost Code", "Bid Number", "Status"}
        imported_count = 0
        skipped_count = 0
        for row in rows:
            if not required.issubset(row.keys()):
                raise ValueError("Import file is missing one or more required columns.")
            candidate = {
                "cost_code": str(row.get("Cost Code", "")).strip(),
                "description": str(row.get("Description", "")).strip(),
                "cost_code_value": str(row.get("Cost Code Value", "0")).strip(),
                "bid_number": str(row.get("Bid Number", "")).strip(),
                "start_date": str(row.get("Start Date", "")).strip(),
                "end_date": str(row.get("End Date", "")).strip(),
                "status": str(row.get("Status", "")).strip(),
            }
            try:
                self._validate_import_task(candidate)
                candidate["id"] = str(uuid.uuid4())
                self.data["tasks"].append(candidate)
                imported_count += 1
            except ValueError:
                skipped_count += 1
        self.save_data()
        self.refresh_all_views()
        messagebox.showinfo(
            "Import Complete",
            f"Imported: {imported_count}\nSkipped: {skipped_count}",
        )

    def _validate_import_task(self, candidate: dict[str, object]) -> None:
        """Validate a candidate task record from imported data."""
        required_values = (
            candidate.get("cost_code", ""),
            candidate.get("bid_number", ""),
            candidate.get("status", ""),
        )
        if not all(required_values):
            raise ValueError("Required imported task fields are missing.")
        if candidate["cost_code"] not in COST_CODE_OPTIONS:
            raise ValueError("Invalid cost code in import data.")
        cost_code_value = safe_float(str(candidate.get("cost_code_value", "0")), "Cost Code Value")
        if cost_code_value < 0:
            raise ValueError("Cost Code Value cannot be negative.")
        if candidate["status"] not in TRACK_STATUSES:
            raise ValueError("Invalid status in import data.")
        if self._find_project_by_job(candidate["bid_number"]) is None:
            raise ValueError("Imported task references unknown bid number.")
        candidate["description"] = COST_CODE_TO_DESCRIPTION[candidate["cost_code"]]
        candidate["cost_code_value"] = cost_code_value
        start_date = candidate.get("start_date", "")
        end_date = candidate.get("end_date", "")
        if start_date and end_date:
            start_obj = parse_date(start_date, "Start Date")
            end_obj = parse_date(end_date, "End Date")
            if end_obj < start_obj:
                raise ValueError("End Date must be on or after Start Date.")
        elif start_date or end_date:
            raise ValueError("Start Date and End Date must both be provided when one is provided.")

    def export_tasks(self) -> None:
        """Export tasks to CSV or XLSX."""
        file_path = filedialog.asksaveasfilename(
            title="Export Tasks",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        headers = ["Cost Code", "Description", "Cost Code Value", "Bid Number", "Start Date", "End Date", "Status", "Duration (Days)"]
        rows = []
        for task in self.data["tasks"]:
            rows.append(
                [
                    task.get("cost_code", ""),
                    task.get("description", ""),
                    task.get("cost_code_value", 0.0),
                    task.get("bid_number", ""),
                    task.get("start_date", ""),
                    task.get("end_date", ""),
                    task.get("status", ""),
                    calculate_duration_days(str(task.get("start_date", "")), str(task.get("end_date", ""))),
                ]
            )
        self._write_table(file_path, headers, rows)
        messagebox.showinfo("Export Complete", "Task export complete.")

    def save_task_template(self) -> None:
        """Save an empty task import template in CSV or XLSX format."""
        file_path = filedialog.asksaveasfilename(
            title="Save Task Template",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        headers = ["Cost Code", "Description", "Cost Code Value", "Bid Number", "Start Date", "End Date", "Status"]
        self._write_table(file_path, headers, [])
        messagebox.showinfo("Template Saved", "Template file created.")

    def refresh_report_filter_values(self) -> None:
        """Update report tab dropdown values based on loaded project data."""
        bids = sorted({str(p.get("bid_number", "")).strip() for p in self.data["projects"] if p.get("bid_number")})
        addresses = sorted({str(p.get("project_address", "")).strip() for p in self.data["projects"] if p.get("project_address")})
        project_types = sorted({str(p.get("project_type", "")).strip() for p in self.data["projects"] if p.get("project_type")})
        estimators = sorted({str(p.get("estimator", "")).strip() for p in self.data["projects"] if p.get("estimator")})
        self.report_bid_combo["values"] = bids
        self.report_address_combo["values"] = addresses
        self.report_project_type_combo["values"] = project_types
        self.report_estimator_combo["values"] = estimators
        self.chart_project_type_combo["values"] = sorted(set(PROJECT_TYPE_OPTIONS).union(project_types))
        self.chart_estimator_combo["values"] = estimators

    def _collect_report_rows(
        self,
        active_only: bool,
        bid_filter: str,
        address_filter: str,
        project_type_filter: str,
        estimator_filter: str,
    ) -> list[dict[str, object]]:
        """Build report rows as one row per project with task-derived schedule totals."""
        rows: list[dict[str, object]] = []
        for project in self.data["projects"]:
            bid_number = str(project.get("bid_number", ""))
            address = str(project.get("project_address", ""))
            project_type = str(project.get("project_type", ""))
            estimator = str(project.get("estimator", ""))
            if bid_filter and bid_filter.lower() not in bid_number.lower():
                continue
            if address_filter and address_filter.lower() not in address.lower():
                continue
            if project_type_filter and project_type_filter.lower() not in project_type.lower():
                continue
            if estimator_filter and estimator_filter.lower() not in estimator.lower():
                continue

            project_tasks = [t for t in self.data["tasks"] if str(t.get("bid_number", "")).strip() == bid_number.strip()]
            if not project_tasks:
                row = {
                    "bid_number": bid_number,
                    "project_address": address,
                    "project_type": project_type,
                    "estimator": estimator,
                    "start_date": "",
                    "end_date": "",
                    "duration_days": 0,
                    "status": "Not Scheduled",
                    "bid_price": float(project.get("bid_price", 0.0)),
                    "job_cost": float(project.get("job_cost", 0.0)),
                    "p_and_l": float(project.get("p_and_l", 0.0)),
                    "p_and_l_percent": float(project.get("p_and_l_percent", 0.0)),
                }
                if not active_only:
                    rows.append(row)
                continue

            valid_tasks: list[dict[str, object]] = []
            for task in project_tasks:
                try:
                    start_text = str(task.get("start_date", "")).strip()
                    end_text = str(task.get("end_date", "")).strip()
                    if start_text and end_text:
                        parse_date(start_text, "Start Date")
                        parse_date(end_text, "End Date")
                    valid_tasks.append(task)
                except ValueError:
                    LOGGER.warning("Skipping report task with invalid dates id=%s", task.get("id"))
            if not valid_tasks:
                continue

            project_status = self._project_status_from_tasks(valid_tasks)
            if active_only and project_status == "Lost":
                continue

            dated_tasks = [
                task
                for task in valid_tasks
                if str(task.get("start_date", "")).strip() and str(task.get("end_date", "")).strip()
            ]
            start_dates = [parse_date(str(task.get("start_date", "")), "Start Date") for task in dated_tasks] if dated_tasks else []
            end_dates = [parse_date(str(task.get("end_date", "")), "End Date") for task in dated_tasks] if dated_tasks else []
            days_total = sum(
                calculate_duration_days(str(task.get("start_date", "")), str(task.get("end_date", "")))
                for task in valid_tasks
            )
            rows.append(
                {
                    "bid_number": bid_number,
                    "project_address": address,
                    "project_type": project_type,
                    "estimator": estimator,
                    "start_date": min(start_dates).isoformat() if start_dates else "",
                    "end_date": max(end_dates).isoformat() if end_dates else "",
                    "duration_days": days_total,
                    "status": project_status,
                    "bid_price": float(project.get("bid_price", 0.0)),
                    "job_cost": float(project.get("job_cost", 0.0)),
                    "p_and_l": float(project.get("p_and_l", 0.0)),
                    "p_and_l_percent": float(project.get("p_and_l_percent", 0.0)),
                }
            )
        return rows

    def run_filtered_report(self) -> None:
        """Run report using filter controls and refresh summary."""
        bid_filter = self.report_bid_combo.get().strip()
        address_filter = self.report_address_combo.get().strip()
        project_type_filter = self.report_project_type_combo.get().strip()
        estimator_filter = self.report_estimator_combo.get().strip()
        rows = self._collect_report_rows(
            self.active_only_var.get(),
            bid_filter,
            address_filter,
            project_type_filter,
            estimator_filter,
        )
        self.report_rows = rows
        self._render_report_rows(rows)
        self._update_summary(rows)

    def show_all_active_projects(self) -> None:
        """Show all active project rows."""
        self.active_only_var.set(True)
        self.report_bid_combo.set("")
        self.report_address_combo.set("")
        self.report_project_type_combo.set("")
        self.report_estimator_combo.set("")
        self.run_filtered_report()

    def show_project_history(self) -> None:
        """Show full project history including completed tasks."""
        self.active_only_var.set(False)
        self.report_bid_combo.set("")
        self.report_address_combo.set("")
        self.report_project_type_combo.set("")
        self.report_estimator_combo.set("")
        self.run_filtered_report()

    def clear_report_filters(self) -> None:
        """Clear report filter fields and show all results."""
        self.active_only_var.set(False)
        self.report_bid_combo.set("")
        self.report_address_combo.set("")
        self.report_project_type_combo.set("")
        self.report_estimator_combo.set("")
        self.run_filtered_report()

    def _render_report_rows(self, rows: list[dict[str, object]]) -> None:
        """Render report rows in the report tree."""
        self.report_tree.delete(*self.report_tree.get_children())
        for idx, row in enumerate(rows):
            self.report_tree.insert(
                "",
                "end",
                iid=f"report::{idx}",
                values=(
                    row["bid_number"],
                    row["project_address"],
                    row["project_type"],
                    row["estimator"],
                    row["start_date"],
                    row["end_date"],
                    row["duration_days"],
                    row["status"],
                    format_currency(float(row["bid_price"])),
                    format_currency(float(row["job_cost"])),
                    format_currency(float(row["p_and_l"])),
                    f"{float(row['p_and_l_percent']):.2f}%",
                ),
            )

    def _update_summary(self, rows: list[dict[str, object]]) -> None:
        """Update summary view section with totals and status counts."""
        total_projects = len(self.data["projects"])
        total_rows = len(rows)
        total_bid = sum(float(r["bid_price"]) for r in rows)
        total_cost = sum(float(r["job_cost"]) for r in rows)
        total_pl = sum(float(r["p_and_l"]) for r in rows)
        status_counts: dict[str, int] = {}
        for row in rows:
            status = str(row["status"])
            status_counts[status] = status_counts.get(status, 0) + 1

        lines = [
            f"Data Mode: {self.data_visibility}",
            f"Total Projects: {total_projects}",
            f"Report Rows: {total_rows}",
            f"Total Bid Price: {format_currency(total_bid)}",
            f"Total Job Cost: {format_currency(total_cost)}",
            f"Total P & L: {format_currency(total_pl)}",
            "",
            "Status Counts:",
        ]
        for status, count in sorted(status_counts.items()):
            lines.append(f"  - {status}: {count}")

        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(lines))
        self.summary_text.configure(state="disabled")

    def export_reports(self) -> None:
        """Export current report rows to CSV or XLSX."""
        file_path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        headers = [
            "Bid Number",
            "Project Address",
            "Project Type",
            "Estimator",
            "Start Date",
            "End Date",
            "Duration (Days)",
            "Status",
            "Bid Price",
            "Job Cost",
            "P & L",
            "P & L %",
        ]
        rows = []
        for row in self.report_rows:
            rows.append(
                [
                    row["bid_number"],
                    row["project_address"],
                    row["project_type"],
                    row["estimator"],
                    row["start_date"],
                    row["end_date"],
                    row["duration_days"],
                    row["status"],
                    row["bid_price"],
                    row["job_cost"],
                    row["p_and_l"],
                    row["p_and_l_percent"],
                ]
            )
        self._write_table(file_path, headers, rows)
        messagebox.showinfo("Export Complete", "Report export complete.")

    def refresh_gantt(self) -> None:
        """Refresh chart details from historical project data."""
        self.gantt_tree.delete(*self.gantt_tree.get_children())
        self.gantt_canvas.delete("all")
        filter_start = parse_date(self._get_date_value(self.gantt_start_filter), "Chart Start Date")
        filter_end = parse_date(self._get_date_value(self.gantt_end_filter), "Chart End Date")
        if filter_end < filter_start:
            raise ValueError("End Date must be on or after Start Date.")
        status_filter = self.chart_status_filter_var.get().strip()
        project_type_filter = self.chart_project_type_combo.get().strip().lower()
        estimator_filter = self.chart_estimator_combo.get().strip().lower()
        sqft_filter_text = self.chart_sqft_entry.get().strip()
        sqft_filter = safe_float(sqft_filter_text, "Approx SqFt") if sqft_filter_text else None

        rows: list[dict[str, object]] = []
        for project in self.data["projects"]:
            bid_number = str(project.get("bid_number", "")).strip()
            if not bid_number:
                continue
            if project_type_filter and project_type_filter not in str(project.get("project_type", "")).lower():
                continue
            if estimator_filter and estimator_filter not in str(project.get("estimator", "")).lower():
                continue

            tasks = [task for task in self.data["tasks"] if str(task.get("bid_number", "")).strip() == bid_number]
            status_value = self._project_status_from_tasks(tasks) if tasks else "Not Scheduled"
            if status_filter and status_filter != "All Statuses" and status_value != status_filter:
                continue

            if sqft_filter is not None:
                sqft_text = str(project.get("project_sqft", "")).strip()
                if not sqft_text:
                    continue
                project_sqft = safe_float(sqft_text, "Project SqFt")
                if abs(project_sqft - sqft_filter) > max(1000.0, sqft_filter * 0.2):
                    continue

            start_candidates: list[date] = []
            end_candidates: list[date] = []
            for task in tasks:
                start_text = str(task.get("start_date", "")).strip()
                end_text = str(task.get("end_date", "")).strip()
                if not (start_text and end_text):
                    continue
                try:
                    start_candidates.append(parse_date(start_text, "Start Date"))
                    end_candidates.append(parse_date(end_text, "End Date"))
                except ValueError:
                    LOGGER.warning("Skipping chart row with invalid dates for task id=%s", task.get("id"))

            if start_candidates and end_candidates:
                start = min(start_candidates)
                end = max(end_candidates)
                if end < filter_start or start > filter_end:
                    continue
                duration = max((end - start).days + 1, 0)
            else:
                duration = int(project.get("duration_days", 0) or 0)

            bid_price = float(project.get("bid_price", 0.0) or 0.0)
            job_cost = float(project.get("job_cost", 0.0) or 0.0)
            p_and_l = float(project.get("p_and_l", bid_price - job_cost) or (bid_price - job_cost))
            p_and_l_percent = float(project.get("p_and_l_percent", self._calculate_pl_percent(bid_price, job_cost)))

            rows.append(
                {
                    "bid_number": bid_number,
                    "address": str(project.get("project_address", "")),
                    "project_type": str(project.get("project_type", "")),
                    "estimator": str(project.get("estimator", "")),
                    "project_sqft": str(project.get("project_sqft", "")).strip(),
                    "start_date": min(start_candidates).isoformat() if start_candidates else "",
                    "end_date": max(end_candidates).isoformat() if end_candidates else "",
                    "duration_days": duration,
                    "bid_price": bid_price,
                    "job_cost": job_cost,
                    "p_and_l": p_and_l,
                    "p_and_l_percent": p_and_l_percent,
                    "status": status_value,
                }
            )
        self.gantt_rows = rows
        for idx, row in enumerate(rows):
            self.gantt_tree.insert(
                "",
                "end",
                iid=f"chart::{idx}",
                values=(
                    row["bid_number"],
                    row["address"],
                    row["project_type"],
                    row["estimator"],
                    row["project_sqft"],
                    row["duration_days"],
                    format_currency(float(row["bid_price"])),
                    format_currency(float(row["job_cost"])),
                    format_currency(float(row["p_and_l"])),
                    f"{float(row['p_and_l_percent']):.2f}%",
                ),
            )
        self._draw_gantt_canvas(rows)

    def clear_chart_filters(self) -> None:
        """Clear chart filters and reload all chart rows."""
        self.chart_project_type_combo.set("")
        self.chart_estimator_combo.set("")
        self.chart_sqft_entry.delete(0, tk.END)
        self.chart_status_combo.set("All Statuses")
        self.chart_option_combo.set("Project")
        self._set_date_value(self.gantt_start_filter, DEFAULT_CHART_START_DATE)
        self._set_date_value(self.gantt_end_filter, DEFAULT_CHART_END_DATE)
        self.refresh_gantt()

    def display_chart(self) -> None:
        """Display matplotlib chart for filtered historical project rows."""
        if plt is None:
            raise ValueError("matplotlib is required to display charts.")
        if not self.gantt_rows:
            raise ValueError("No chart rows are available for the current filter.")

        rows = sorted(
            self.gantt_rows,
            key=lambda row: (str(row.get("start_date", "")).strip(), str(row.get("bid_number", "")).strip()),
        )
        chart_option = self.chart_option_combo.get().strip() or "Project"

        if chart_option == "Project":
            labels = [str(row["bid_number"]) for row in rows]
            bid_prices = [float(row["bid_price"]) for row in rows]
            job_costs = [float(row["job_cost"]) for row in rows]
            x_positions = list(range(len(labels)))
            bar_width = 0.4

            _, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            bid_bars = ax1.bar(
                [x - (bar_width / 2) for x in x_positions],
                bid_prices,
                width=bar_width,
                color="#90CAF9",
                label="Bid Price",
            )
            job_bars = ax1.bar(
                [x + (bar_width / 2) for x in x_positions],
                job_costs,
                width=bar_width,
                color="#FFCC80",
                alpha=0.95,
                label="Job Cost",
            )
            ax1.set_ylabel("Amount ($)")
            ax1.set_title("Historical Bid Price vs Job Cost (Grouped by Bid Number)")
            ax1.legend(loc="upper right")
            ax1.grid(axis="y", linewidth=0.3)

            bid_line, = ax2.plot(x_positions, bid_prices, marker="o", color="#1E88E5", label="Bid Price")
            job_line, = ax2.plot(x_positions, job_costs, marker="o", color="#FB8C00", label="Job Cost")
            ax2.set_ylabel("Amount ($)")
            ax2.set_xlabel("Bid Number")
            ax2.grid(axis="y", linewidth=0.3)
            ax2.legend(loc="upper right")
            ax2.set_xticks(x_positions)
            ax2.set_xticklabels(labels, rotation=35, ha="right")

            if mplcursors is not None:
                bar_cursor = mplcursors.cursor([*bid_bars.patches, *job_bars.patches], hover=True)

                @bar_cursor.connect("add")
                def _on_add_project_bar(sel) -> None:
                    patch = sel.artist
                    x_center = patch.get_x() + (patch.get_width() / 2)
                    bid_index = int(round(x_center))
                    bid_index = max(0, min(bid_index, len(labels) - 1))
                    dataset = "Bid Price" if patch in bid_bars.patches else "Job Cost"
                    amount = patch.get_height()
                    sel.annotation.set_text(f"{labels[bid_index]}\n{dataset}: {format_currency(float(amount))}")

                line_cursor = mplcursors.cursor([bid_line, job_line], hover=True)

                @line_cursor.connect("add")
                def _on_add_project_line(sel) -> None:
                    point_index = int(sel.index)
                    point_index = max(0, min(point_index, len(labels) - 1))
                    dataset = "Bid Price" if sel.artist is bid_line else "Job Cost"
                    amount = bid_prices[point_index] if dataset == "Bid Price" else job_costs[point_index]
                    sel.annotation.set_text(f"{labels[point_index]}\n{dataset}: {format_currency(float(amount))}")

            plt.tight_layout()
            plt.show()
            return

        if chart_option == "Estimator":
            estimator_totals: dict[str, dict[str, float]] = defaultdict(
                lambda: {"bid_price": 0.0, "job_cost": 0.0, "p_and_l": 0.0, "bids": 0.0}
            )
            for row in rows:
                estimator_name = str(row.get("estimator", "")).strip() or "Unassigned"
                estimator_totals[estimator_name]["bid_price"] += float(row["bid_price"])
                estimator_totals[estimator_name]["job_cost"] += float(row["job_cost"])
                estimator_totals[estimator_name]["p_and_l"] += float(row["p_and_l"])
                estimator_totals[estimator_name]["bids"] += 1.0

            labels = sorted(estimator_totals.keys())
            bid_prices = [estimator_totals[label]["bid_price"] for label in labels]
            job_costs = [estimator_totals[label]["job_cost"] for label in labels]
            bid_counts = [int(estimator_totals[label]["bids"]) for label in labels]
            p_and_l_values = [estimator_totals[label]["p_and_l"] for label in labels]
            x_positions = list(range(len(labels)))
            bar_width = 0.35

            _, axes = plt.subplots(2, 2, figsize=(13, 9))
            ax_bar, ax_line, ax_pie, ax_metrics = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

            estimator_bid_bars = ax_bar.bar(
                [x - (bar_width / 2) for x in x_positions],
                bid_prices,
                width=bar_width,
                color="#64B5F6",
                label="Total Bid Price",
            )
            estimator_job_bars = ax_bar.bar(
                [x + (bar_width / 2) for x in x_positions],
                job_costs,
                width=bar_width,
                color="#FFB74D",
                label="Total Job Cost",
            )
            ax_bar.set_xticks(x_positions)
            ax_bar.set_xticklabels(labels, rotation=20, ha="right")
            ax_bar.set_title("Estimator Totals")
            ax_bar.set_ylabel("Amount ($)")
            ax_bar.legend(loc="upper right")
            ax_bar.grid(axis="y", linewidth=0.3)

            estimator_bid_line, = ax_line.plot(x_positions, bid_counts, marker="o", color="#7E57C2", label="Number of Bids")
            ax_line.set_xticks(x_positions)
            ax_line.set_xticklabels(labels, rotation=20, ha="right")
            ax_line.set_title("Bids per Estimator")
            ax_line.set_ylabel("Count")
            ax_line.grid(axis="y", linewidth=0.3)
            ax_line.legend(loc="upper right")

            total_bid_price = sum(bid_prices)
            total_job_cost = sum(job_costs)
            ax_pie.pie(
                [total_bid_price, total_job_cost],
                labels=["Total Bid Price", "Total Job Cost"],
                autopct="%1.1f%%",
                colors=["#64B5F6", "#FFB74D"],
            )
            ax_pie.set_title("Bid vs Job Cost Distribution")

            estimator_pl_bars = ax_metrics.bar(x_positions, p_and_l_values, color="#66BB6A")
            ax_metrics.set_xticks(x_positions)
            ax_metrics.set_xticklabels(labels, rotation=20, ha="right")
            ax_metrics.set_title("Total P & L by Estimator")
            ax_metrics.set_ylabel("P & L ($)")
            ax_metrics.grid(axis="y", linewidth=0.3)

            if mplcursors is not None:
                estimator_totals_cursor = mplcursors.cursor(
                    [*estimator_bid_bars.patches, *estimator_job_bars.patches],
                    hover=True,
                )

                @estimator_totals_cursor.connect("add")
                def _on_add_estimator_totals(sel) -> None:
                    patch = sel.artist
                    x_center = patch.get_x() + (patch.get_width() / 2)
                    estimator_index = int(round(x_center))
                    estimator_index = max(0, min(estimator_index, len(labels) - 1))
                    dataset = "Total Bid Price" if patch in estimator_bid_bars.patches else "Total Job Cost"
                    amount = patch.get_height()
                    sel.annotation.set_text(f"{labels[estimator_index]}\n{dataset}: {format_currency(float(amount))}")

                estimator_bids_cursor = mplcursors.cursor([estimator_bid_line], hover=True)

                @estimator_bids_cursor.connect("add")
                def _on_add_estimator_bids(sel) -> None:
                    point_index = int(sel.index)
                    point_index = max(0, min(point_index, len(labels) - 1))
                    sel.annotation.set_text(f"{labels[point_index]}\nNumber of Bids: {bid_counts[point_index]}")

                estimator_pl_cursor = mplcursors.cursor(estimator_pl_bars.patches, hover=True)

                @estimator_pl_cursor.connect("add")
                def _on_add_estimator_pl(sel) -> None:
                    patch = sel.artist
                    x_center = patch.get_x() + (patch.get_width() / 2)
                    estimator_index = int(round(x_center))
                    estimator_index = max(0, min(estimator_index, len(labels) - 1))
                    sel.annotation.set_text(
                        f"{labels[estimator_index]}\nTotal P & L: {format_currency(float(patch.get_height()))}"
                    )

            plt.tight_layout()
            plt.show()
            return

        status_totals: dict[str, dict[str, float]] = defaultdict(
            lambda: {"bid_price": 0.0, "job_cost": 0.0, "p_and_l": 0.0, "bids": 0.0}
        )
        for row in rows:
            status_value = str(row.get("status", "")).strip() or "Unknown"
            status_totals[status_value]["bid_price"] += float(row["bid_price"])
            status_totals[status_value]["job_cost"] += float(row["job_cost"])
            status_totals[status_value]["p_and_l"] += float(row["p_and_l"])
            status_totals[status_value]["bids"] += 1.0

        labels = sorted(status_totals.keys())
        bid_prices = [status_totals[label]["bid_price"] for label in labels]
        job_costs = [status_totals[label]["job_cost"] for label in labels]
        bid_counts = [int(status_totals[label]["bids"]) for label in labels]
        x_positions = list(range(len(labels)))
        bar_width = 0.35

        _, axes = plt.subplots(2, 2, figsize=(13, 9))
        ax_bar, ax_line, ax_pie, ax_metrics = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

        status_bid_bars = ax_bar.bar(
            [x - (bar_width / 2) for x in x_positions],
            bid_prices,
            width=bar_width,
            color="#90CAF9",
            label="Total Bid Price",
        )
        status_job_bars = ax_bar.bar(
            [x + (bar_width / 2) for x in x_positions],
            job_costs,
            width=bar_width,
            color="#FFCC80",
            label="Total Job Cost",
        )
        ax_bar.set_xticks(x_positions)
        ax_bar.set_xticklabels(labels)
        ax_bar.set_title("Status Totals")
        ax_bar.set_ylabel("Amount ($)")
        ax_bar.legend(loc="upper right")
        ax_bar.grid(axis="y", linewidth=0.3)

        ax_line.plot(x_positions, bid_counts, marker="o", color="#5C6BC0", label="Number of Bids")
        ax_line.set_xticks(x_positions)
        ax_line.set_xticklabels(labels)
        ax_line.set_title("Bids per Status")
        ax_line.set_ylabel("Count")
        ax_line.grid(axis="y", linewidth=0.3)
        ax_line.legend(loc="upper right")

        ax_pie.pie(
            bid_counts,
            labels=labels,
            autopct="%1.1f%%",
            colors=["#66BB6A", "#EF5350", "#FFA726", "#9575CD"][: len(labels)],
        )
        ax_pie.set_title("Bid Count Share by Status")

        status_bid_only_bars = ax_metrics.bar(x_positions, bid_prices, color="#26A69A")
        ax_metrics.set_xticks(x_positions)
        ax_metrics.set_xticklabels(labels)
        ax_metrics.set_title("Total Bid Price by Status")
        ax_metrics.set_ylabel("Bid Price ($)")
        ax_metrics.grid(axis="y", linewidth=0.3)

        if mplcursors is not None:
            status_totals_cursor = mplcursors.cursor([*status_bid_bars.patches, *status_job_bars.patches], hover=True)

            @status_totals_cursor.connect("add")
            def _on_add_status_totals(sel) -> None:
                patch = sel.artist
                x_center = patch.get_x() + (patch.get_width() / 2)
                status_index = int(round(x_center))
                status_index = max(0, min(status_index, len(labels) - 1))
                dataset = "Total Bid Price" if patch in status_bid_bars.patches else "Total Job Cost"
                amount = patch.get_height()
                sel.annotation.set_text(f"{labels[status_index]}\n{dataset}: {format_currency(float(amount))}")

            status_bid_price_cursor = mplcursors.cursor(status_bid_only_bars.patches, hover=True)

            @status_bid_price_cursor.connect("add")
            def _on_add_status_bid_price(sel) -> None:
                patch = sel.artist
                x_center = patch.get_x() + (patch.get_width() / 2)
                status_index = int(round(x_center))
                status_index = max(0, min(status_index, len(labels) - 1))
                sel.annotation.set_text(
                    f"{labels[status_index]}\nTotal Bid Price: {format_currency(float(patch.get_height()))}"
                )

        plt.tight_layout()
        plt.show()

    def _draw_gantt_canvas(self, rows: list[dict[str, object]]) -> None:
        """Draw a simple text preview for chart-ready rows."""
        width = max(1020, int(self.gantt_canvas.winfo_width()))
        height = max(300, int(self.gantt_canvas.winfo_height()))
        self.gantt_canvas.configure(scrollregion=(0, 0, width, height))
        if not rows:
            self.gantt_canvas.create_text(
                width // 2,
                height // 2,
                text="No chart data available for the selected filters.",
                fill="#666666",
                font=("Segoe UI", 12),
            )
            return

        total_bid = sum(float(row["bid_price"]) for row in rows)
        total_cost = sum(float(row["job_cost"]) for row in rows)
        total_pl = sum(float(row["p_and_l"]) for row in rows)
        total_pl_percent = sum(float(row["p_and_l_percent"]) for row in rows)
        row_count = len(rows)
        average_bid = total_bid / row_count if row_count else 0.0
        average_cost = total_cost / row_count if row_count else 0.0
        average_pl = total_pl / row_count if row_count else 0.0
        average_pl_percent = total_pl_percent / row_count if row_count else 0.0

        summary_lines = [
            f"Matching Projects: {len(rows)}",
            "Totals:",
            f"Total Bid Price: {format_currency(total_bid)}",
            f"Total Job Cost: {format_currency(total_cost)}",
            f"Total P & L: {format_currency(total_pl)}",
            "Averages:",
            f"Average Bid Price: {format_currency(average_bid)}",
            f"Average Job Cost: {format_currency(average_cost)}",
            f"Average P & L: {format_currency(average_pl)}",
            f"Average P & L %: {average_pl_percent:.2f}%",
            "",
            "Click 'Display Chart' to open Matplotlib chart.",
        ]
        self.gantt_canvas.create_rectangle(15, 15, width - 15, height - 15, outline="#b0bec5", fill="#f8fbff")
        self.gantt_canvas.create_text(
            30,
            35,
            anchor="nw",
            text="\n".join(summary_lines),
            fill="#1f2937",
            font=("Segoe UI", 11),
        )

    def refresh_map(self) -> None:
        """Refresh map canvas and active location list from active tasks."""
        self.map_tree.delete(*self.map_tree.get_children())
        self.map_canvas.delete("all")
        active_rows = []
        unique_jobs: dict[tuple[str, str], dict[str, object]] = {}
        for task in self.data["tasks"]:
            if str(task.get("status", "")) == "Lost":
                continue
            project = self._find_project_by_job(str(task.get("bid_number", "")))
            if project is None:
                continue
            bid_number = str(task.get("bid_number", "")).strip()
            address = str(project.get("project_address", "")).strip()
            if not address:
                continue
            key = (bid_number, address)
            if key not in unique_jobs:
                unique_jobs[key] = {
                    "bid_number": bid_number,
                    "project_address": address,
                    "status": str(task.get("status", "")).strip(),
                }
        active_rows = list(unique_jobs.values())
        if not active_rows:
            self.map_canvas.create_text(
                500,
                160,
                text="No active locations available.",
                fill="#666666",
                font=("Segoe UI", 12),
            )
            return

        width = max(1020, int(self.map_canvas.winfo_width()))
        height = max(320, int(self.map_canvas.winfo_height()))
        self.map_canvas.create_rectangle(10, 10, width - 10, height - 10, outline="#b0bec5", fill="#e3f2fd")
        self.map_canvas.create_text(20, 20, anchor="nw", text="Map View (active project locations)", font=("Segoe UI", 11, "bold"))

        marker_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        displayed_addresses: list[str] = []
        for idx, row in enumerate(active_rows):
            marker = marker_letters[idx % len(marker_letters)]
            displayed_addresses.append(f"{marker}. {row['project_address']}")
            self.map_tree.insert(
                "",
                "end",
                iid=f"map::{idx}",
                values=(marker, row["bid_number"], row["project_address"], row["status"]),
            )

        columns = 2
        col_width = (width - 50) // columns
        base_y = 50
        for idx, text in enumerate(displayed_addresses):
            col = idx % columns
            row_index = idx // columns
            x = 25 + col * col_width
            y = base_y + row_index * 28
            self.map_canvas.create_oval(x, y, x + 16, y + 16, fill="#ef5350", outline="")
            self.map_canvas.create_text(x + 8, y + 8, text=text[0], fill="white", font=("Segoe UI", 8, "bold"))
            self.map_canvas.create_text(x + 22, y + 8, text=text[3:], anchor="w", font=("Segoe UI", 9))

    def _write_table(self, file_path: str, headers: list[str], rows: list[list[object]]) -> None:
        """Write tabular data to CSV or XLSX based on file extension."""
        _, ext = os.path.splitext(file_path.lower())
        if ext == ".csv":
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(rows)
            return
        if ext == ".xlsx":
            if Workbook is None:
                raise ValueError("openpyxl is required for .xlsx export.")
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Export"
            sheet.append(headers)
            for row in rows:
                sheet.append(row)
            workbook.save(file_path)
            return
        raise ValueError("Unsupported file extension.")

    def _read_table(self, file_path: str) -> list[dict[str, object]]:
        """Read CSV or XLSX tabular data and return rows as dictionaries."""
        _, ext = os.path.splitext(file_path.lower())
        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                return [dict(row) for row in reader]
        if ext == ".xlsx":
            if load_workbook is None:
                raise ValueError("openpyxl is required for .xlsx import.")
            workbook = load_workbook(file_path)
            sheet = workbook.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(value).strip() if value is not None else "" for value in rows[0]]
            result: list[dict[str, object]] = []
            for raw_row in rows[1:]:
                mapped = {}
                for idx, header in enumerate(headers):
                    mapped[header] = raw_row[idx] if idx < len(raw_row) else None
                result.append(mapped)
            return result
        raise ValueError("Unsupported import file extension.")


def main() -> None:
    """Start the Project Management GUI."""
    root = tk.Tk()
    app = ProjectManagementApp(root)
    def _handle_tk_exception(exc_type, exc_value, exc_traceback) -> None:
        """Handle uncaught Tk callbacks with sanitized user notifications."""
        LOGGER.exception("Tk callback exception", exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror("Application Error", "An unexpected application error occurred.")

    root.report_callback_exception = _handle_tk_exception
    root.mainloop()


if __name__ == "__main__":
    main()

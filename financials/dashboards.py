import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter import messagebox, ttk

from monthly_sales import monthly_sales
from expenses import quickbooks_monthly_expenses

# ========================================================================== #
# ================================== INFO ================================== #
# ========================================================================== #
# 
# ========================================================================== #
# ================================== TODO ================================== #
# ========================================================================== #
# TODO: 
# ========================================================================== #

project_data = pd.read_csv("financials/sample_data/test_company_project_data_(02122026).csv")
expenses_data = pd.read_csv("financials/sample_data/test_company_expenses.csv")
sales_by_customer = pd.read_excel("financials/sample_data/test_company_sales by customer summary (2025).xlsx", engine="openpyxl")
ar_aging_summary = pd.read_excel("financials/sample_data/test_company_ar_aging summary report.xlsx", engine="openpyxl")
ap_aging_summary = pd.read_excel("financials/sample_data/test_company_ap_ aging summary report.xlsx", engine="openpyxl")

ar_aging_summary = ar_aging_summary.fillna(0)
ap_aging_summary = ap_aging_summary.fillna(0)


# print(project_data.head())
# print(project_data.info())
# print(project_data.describe())
# print(project_data.shape)
# print(project_data.columns)

# print(expenses_data.head())
# print(expenses_data.describe())
# print(expenses_data.info())

# print(ar_aging_summary.head())
# print(ar_aging_summary.info())
# print(ar_aging_summary.describe())
# print(ar_aging_summary.shape)
# print(ar_aging_summary.columns)

# print(ap_aging_summary.head())
# print(ap_aging_summary.info())
# print(ap_aging_summary.describe())
# print(ap_aging_summary.shape)
# print(ap_aging_summary.columns)

# ============================================================================ #
# =========================== ESTIMATOR DASHBOARD ============================ #
# ============================================================================ #

def display_estimator_dashboard():
    """
    Display the estimator dashboard in the application.

    This function initializes and displays the estimator dashboard, providing
    users with an overview of current projects, key metrics, and quick access
    to estimation tools. It sets up the necessary widgets, layouts, and event
    handlers for user interaction within the dashboard.

    Parameters:
    None

    Returns:
    None
    """
    expenses_data['Total'] = pd.to_numeric(expenses_data['Total'], errors='coerce')
    top_expenses = expenses_data.groupby('Expenses')['Total'].sum().nlargest(10)

    top_customers = sales_by_customer.groupby('Customer')['Total'].sum().nlargest(10)

    # For each 'estimator' in the project_data file sum and print the results.
    # Group by 'estimator' and sum 'bid_price'
    grouped_by_estimator = project_data.groupby('Estimator')['Bid Price'].sum()

    # Loop through and print the results
    # for estimator, total_bid_price in grouped_by_estimator.items():
    #     print(f"Estimator: {estimator}")
    #     print(f"    Total Sales: ${total_bid_price:,.2f}")

    # For each description in 'project_description'sum the 'bid_price' and print the results
    grouped_by_description = project_data.groupby('Description')['Bid Price'].sum()

    # for description, total_bid_price in grouped_by_description.items():
    #     print(f"Description: {description}")
    #     print(f"    Total Sales ${total_bid_price:,.2f}")

    # Create subplot grid: 2 rows, 2 columns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Sales by Estimator",
            "Profit % by Project Description",
            "Bid Price & Job Cost by Estimator",
            "Top 10 Sales by Customer"
        ),
        specs = [
            [{"type": "domain"}, {"type": "domain"}], # Pie Chart
            [{"type": "xy"}, {"type": "domain"}], # Bar chart, Pie Chart
        ]
    )

    # Top left: Pie chart for sales_by_estimator
    fig.add_trace(
        go.Pie(
            labels=grouped_by_estimator.index,
            values=grouped_by_estimator.values,
            name="Sales by Estimator",
            legendgroup="estimator"
        ),
        row=1, col=1
    )

    # Top right: Pie chart for sales_by_project_description (profit %)
    fig.add_trace(
        go.Pie(
            labels=grouped_by_description.index,
            values=grouped_by_description.values,
            name="Profit % by Description",
            legendgroup="description"
        ),
        row=1, col=2
    )

    # Bottom left: Grouped bar chart for bid_price and job_cost by estimator
    estimators = project_data['Estimator'].unique()
    bid_prices = project_data.groupby('Estimator')['Bid Price'].sum()
    job_costs = project_data.groupby('Estimator')['Job Cost'].sum()

    fig.add_trace(
        go.Bar(
            x=estimators,
            y=bid_prices[estimators],
            name="Bid Price"
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(
            x=estimators,
            y=job_costs[estimators],
            name="Job Cost"
        ),
        row=2, col=1
    )

    # Bottom right: Pie chart for top 10 sales_by_customer
    top_10_customers = top_customers.nlargest(10)
    fig.add_trace(
        go.Pie(
            labels=top_10_customers.index,
            values=top_10_customers.values,
            name="Top 10 Customers",
            legendgroup="customer"
        ),
        row=2, col=2
    )

    # Update layout for grouped bar chart
    fig.update_layout(
    barmode='group',
    height=800,
    width=1200,
    title={
        'text': "Estimator Dashboard",
        'x': 0.5,  # Center the title
        'xanchor': 'center'
        }
    )

    fig.show()

# ============================================================================ #
# =========================== FINANCIAL DASHBOARD ============================ #
# ============================================================================ #

def display_financial_dashboard():
    """
    Display the financial dashboard in the application.

    This function initializes and presents the financial dashboard, offering users
    a summary of financial data such as project budgets, expenses, revenues, and
    other key financial metrics. It sets up the necessary widgets, charts, and
    layouts to visualize financial information and provides tools for financial
    analysis and reporting.

    Parameters:
    None

    Returns:
    None
    """
    # Get last 12 months' keys
    last_12_months = list(monthly_sales.keys())[-12:]
    sales_last_12 = [monthly_sales[k] for k in last_12_months]
    expenses_last_12 = [quickbooks_monthly_expenses.get(k, 0) for k in last_12_months]

    # Calculate top 10 customers
    top_customers = sales_by_customer.groupby('Customer')['Total'].sum().nlargest(10)
    grouped = project_data.groupby('Description').agg({'Bid Price': 'sum', 'Job Cost': 'sum'}).reset_index()

    # KPIs
    total_revenue = round(sum(sales_last_12), 2)
    gross_profit = round(sum(sales_last_12) - sum(expenses_last_12), 2)

    _30_days_ar = ar_aging_summary['1 - 30'].sum()
    _60_days_ar = ar_aging_summary['61 - 90'].sum()
    _90_days_ar = ar_aging_summary['91 AND OVER'].sum()
    total_receivables_due = round(ar_aging_summary['Total'].sum(), 2)

    # print(f"30 days = ${_30_days_ar:,.2f}")
    # print(f"60 days = ${_60_days_ar:,.2f}")
    # print(f"90 days = ${_90_days_ar:,.2f}")
    # print(f"Total Receivables = ${total_receivables_due:,.2f}")

    # Create subplot: 6 rows, 3 columns
    fig = make_subplots(
        rows=6, cols=3,
        vertical_spacing=0.05,
        column_widths=[0.2, 0.4, 0.4],
        row_heights=[0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
        specs=[
            [{"type": "domain"}, {"type": "xy", "rowspan": 3}, {"type": "xy", "rowspan": 3}],  # Row 1
            [{"type": "domain"}, None, None], # Row 2
            [{"type": "domain"}, None, None], # Row 3
            [{"type": "domain"}, {"type": "xy", "rowspan": 3}, {"type": "domain", "rowspan": 3}], # Row 4
            [{"type": "domain"}, None, None], # Row 5
            [{"type": "domain"}, None, None], # Row 6
        ],
        subplot_titles=[
            None, "Sales vs Expenses (Top) | Bid Price vs Job Cost by Description (Bottom)", 
            "Sales & Expenses (Top) | Top 10 Customers (Bottom)",
            None, None, None,
            None, None, None,
            None, None, None,
            None, None, None,
            None, None, None,
        ]
    )

    # KPIs in left column
    fig.add_trace(go.Indicator(
        mode="number", 
        value=total_revenue, 
        title={"text": "Total Revenue"}, 
        number={"valueformat": ",.0f"}
        ),  
        row=1, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=gross_profit, 
        title={"text": "Gross Profit"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=2, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=total_receivables_due, 
        title={"text": "Total Receivables Due"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=3, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_30_days_ar, 
        title={"text": "30 Days AR"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=4, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_60_days_ar, 
        title={"text": "60 Days AR"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=5, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_90_days_ar, 
        title={"text": "90+ Days AR"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=6, col=1)

    # Grouped horizontal bar chart in top middle (row 1, col 2)
    fig.add_trace(go.Bar(
        y=last_12_months,
        x=sales_last_12,
        name='Sales',
        orientation='h',
        marker_color='blue'
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        y=last_12_months,
        x=expenses_last_12,
        name='Expenses',
        orientation='h',
        marker_color='orange'
    ), row=1, col=2)

    fig.update_layout(
        barmode='group',
        height=1200,
        width=2200,
        showlegend=True,
        title={
            'text': 'Financial Dashboard',
            'x': 0.5, # Center the title
            'xanchor': 'center', # Anchor the title at the center
        },
        # title_text="Financial Dashboard",
        font=dict(size=14),
        title_font=dict(size=20),
    )

    # Add grouped bar chart to bottom middle (row 6, col 2)
    fig.add_trace(go.Bar(
        y=grouped['Description'],
        x=grouped['Bid Price'],
        name='Bid Price',
        orientation='h',
        marker_color='blue'
    ), row=4, col=2)

    fig.add_trace(go.Bar(
        y=grouped['Description'],
        x=grouped['Job Cost'],
        name='Job Cost',
        orientation='h',
        marker_color='orange'
    ), row=4, col=2)

    # Add line chart to top right (row 1, col 3)
    fig.add_trace(go.Scatter(
        x=last_12_months,
        y=sales_last_12,
        mode='lines+markers',
        name='Monthly Sales',
        line=dict(color='blue')
    ), row=1, col=3)

    fig.add_trace(go.Scatter(
        x=last_12_months,
        y=expenses_last_12,
        mode='lines+markers',
        name='Monthly Expenses',
        line=dict(color='orange')
    ), row=1, col=3)

    # Add pie chart to bottom right (row 6, col 3)
    fig.add_trace(go.Pie(
        labels=top_customers.index,
        values=top_customers.values,
        name='Top 10 Customers',
        hole=0.4
    ), row=4, col=3)

    fig.show()

# ============================================================================ #
# ============================== AR DASHBOARD ================================ #
# ============================================================================ #

def display_ar_dashboard():
    """
    Display the accounts receivable (AR) dashboard in the application.

    This function initializes and displays the AR dashboard, providing users with
    an overview of outstanding invoices, payment statuses, aging reports, and other
    key accounts receivable metrics. It sets up the necessary widgets, tables, and
    visualizations to help users monitor and manage receivables efficiently.

    Parameters:
    None

    Returns:
    None
    """
    current_ar = ar_aging_summary['CURRENT'].sum()
    _1_to_30_ar = ar_aging_summary['1 - 30'].sum()
    _31_to_60_ar = ar_aging_summary['31 - 60'].sum()
    _61_to_90_ar = ar_aging_summary['61 - 90'].sum()
    _91_and_over_ar = ar_aging_summary['91 AND OVER'].sum()
    total_receivables_due = round(ar_aging_summary['Total'].sum(), 2)

    # Calculate top 10 customers
    top_customers = sales_by_customer.groupby('Customer')['Total'].sum().nlargest(10)

    # Prepare DataFrame for plotting
    top_customers_df = top_customers.reset_index().rename(columns={'Total': 'Sales'})

    # Merge with AR aging summary to get AR total for those customers (fill NaN with 0)
    top_customers_df = top_customers_df.merge(
        ar_aging_summary[['Customer', 'Total']].rename(columns={'Total': 'AR Due'}),
        on='Customer',
        how='left'
    ).fillna({'AR Due': 0})

    # Prepare data for grouped bar chart
    customers = top_customers_df['Customer']
    sales = top_customers_df['Sales']
    ar_due = top_customers_df['AR Due']

    # Prepare data for the pie chart
    aging_buckets = ['CURRENT', '1 - 30', '31 - 60', '61 - 90', '91 AND OVER']  # Add more if your data has more columns
    bucket_sums = [ar_aging_summary[col].sum() for col in aging_buckets]

    # Create subplot: 6 rows, 3 columns
    fig = make_subplots(
        rows=6, cols=3,
        vertical_spacing=0.05,
        column_widths=[0.2, 0.4, 0.4],
        row_heights=[0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
        specs=[
            [{"type": "domain"}, {"type": "xy", "rowspan": 3}, {"type": "domain", "rowspan": 3}],  # Row 1
            [{"type": "domain"}, None, None], # Row 2
            [{"type": "domain"}, None, None], # Row 3
            [{"type": "domain"}, {"type": "table", "rowspan": 3}, {"type": "xy", "rowspan": 3}], # Row 4
            [{"type": "domain"}, None, None], # Row 5
            [{"type": "domain"}, None, None], # Row 6
        ],
        subplot_titles=[
            None, "Aging Summary by Top 10 Customers (Top) | Aging Summary Table (Bottom)", None, 
            None, None, None,
            None, None, None,
            None, None, None,
            None, None, None,
            None, None, None,
            None, None, None,
        ]
    )

    # KPIs in left column
    fig.add_trace(go.Indicator(
        mode="number", 
        value=current_ar, 
        title={"text": "Current"}, 
        number={"valueformat": ",.0f"}
        ),  
        row=1, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_1_to_30_ar, 
        title={"text": "1 - 30"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=2, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_31_to_60_ar, 
        title={"text": "31 - 60"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=3, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_61_to_90_ar, 
        title={"text": "61 - 90"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=4, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=_91_and_over_ar, 
        title={"text": "91 AND OVER"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=5, col=1)
    fig.add_trace(go.Indicator(
        mode="number", 
        value=total_receivables_due, 
        title={"text": "Total Receivables Due"}, 
        number={"valueformat": ",.0f"}
        ), 
        row=6, col=1)
    
    # Add grouped horizontal bar chart to top left (row=1, col=2)
    fig.add_trace(
        go.Bar(
            y=customers,
            x=sales,
            name='Sales',
            orientation='h',
            marker_color='steelblue'
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(
            y=customers,
            x=ar_due,
            name='AR Due',
            orientation='h',
            marker_color='indianred'
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Amount", row=1, col=1)
    fig.update_yaxes(title_text="Customer", row=1, col=1)
    fig.update_layout(barmode='group')

    # Add pie chart to the top right (row=1, col=3)
    fig.add_trace(
        go.Pie(
            labels=aging_buckets,
            values=bucket_sums,
            hole=0.4,
            title="AR Aging Summary"
        ),
        row=1, col=3
    )
        
    # Add the table to the bottom row, second column
    fig.add_trace(
        go.Table(
            header=dict(
                values=list(ar_aging_summary.columns),
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[ar_aging_summary[col] for col in ar_aging_summary.columns],
                fill_color='lavender',
                align='left'
            )
        ),
        row=4, col=2,
    )

    # Add line chart to the bottom right (row=6, col=3)
    fig.add_trace(
        go.Scatter(
            x=aging_buckets,
            y=bucket_sums,
            mode='lines+markers',
            name='AR Aging Over Time',
            line=dict(color='royalblue', width=3)
        ),
        row=4, col=3
    )

    fig.update_xaxes(title_text="Aging", row=4, col=3)
    fig.update_yaxes(title_text="Total Amount", row=4, col=3)

    fig.update_layout(
        height=1200,
        width=2200,
        showlegend=True,
        title={
            'text': 'AR Aging Dashboard',
            'x': 0.5,
            'xanchor': 'center', 
        },
        font=dict(size=14),
        title_font=dict(size=20),
    )
    
    fig.show()

# ============================================================================ #
# ================================ AP DASHBOARD ============================== #
# ============================================================================ #

def display_ap_dashboard():
    pass

# ============================================================================ #
# ================================ DISPLAY CHARTS ============================ #
# ============================================================================ #

def display_chart():
    option = options.get()

    if option == 'Estimator Dashboard':
        display_estimator_dashboard()
    elif option == 'Financial Dashboard':
        display_financial_dashboard()
    elif option == 'A/R Dashboard':
        display_ar_dashboard()
    elif option == 'A/P Dashboard':
        display_ap_dashboard()

# ============================================================================ #
# ==================================== GUI =================================== #
# ============================================================================ #

root = tk.Tk()
root.minsize(width=100, height=100)
root.title("Company Dashboard")
root.config(padx=25, pady=25)

options = ttk.Combobox(root, width=25, state="readonly",
                       values=[
                           "Estimator Dashboard",
                           "Financial Dashboard",
                           "A/R Dashboard",
                           "A/P Dashboard",
                            ]
                       )

options.grid(column=1, row=1, padx=5, pady=10)
options_label = tk.Label(text="Options")
options_label.grid(column=2, row=1, padx=5, pady=10)

chart_button = tk.Button(root, text="Display Chart", command=display_chart)
chart_button.grid(column=1, row=2, padx=5, pady=5)

root.mainloop()

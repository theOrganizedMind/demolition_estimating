import statistics
import logging
import matplotlib.pyplot as plt
import matplotlib as mpl
import mplcursors
import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from revenue import revenue
from postgresql import get_db_connection


logger = logging.getLogger(__name__)

# ========================================================================== #
# ================================== INFO ================================== #
# ========================================================================== #
# Description of the Program:
# ========================================================================== #
# ================================== TODO ================================== #
# ========================================================================== #
# TODO: 
# Add PostgreSQL variables to .env before running program. 
# See postgresql.py for required parameters.
# ========================================================================== #

NUM_MONTHS = 12
WORK_DAYS_IN_MONTH = 20
DAILY_WORK_HOURS = 10
PROFIT_MARGIN = 1.35
NUM_EMPLOYEES = 112

# =========================================================================== #
# ======================== Get Data from PostgreSQL ========================= #
# =========================================================================== #

def fetch_monthly_numbers_from_postgresql(start_date, end_date):
    """Fetch monthly financial values between start/end month, inclusive."""
    start_month = datetime.strptime(start_date, '%Y-%m').strftime('%Y-%m')
    end_month = datetime.strptime(end_date, '%Y-%m').strftime('%Y-%m')

    query = """
        SELECT
            year_month,
            disposalcost AS monthly_disposal_cost,
            expense AS quickbooks_monthly_expenses,
            sales AS monthly_sales,
            payroll AS monthly_payroll
        FROM monthly_numbers
        WHERE year_month >= %(start_month)s
          AND year_month <= %(end_month)s
        ORDER BY year_month;
    """

    with get_db_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params={"start_month": start_month, "end_month": end_month},
        )

    if df.empty:
        raise ValueError(
            "No monthly_numbers records found for the selected date range."
        )

    df['year_month'] = df['year_month'].astype(str)
    for col in [
        'monthly_disposal_cost',
        'quickbooks_monthly_expenses',
        'monthly_sales',
        'monthly_payroll',
    ]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    return df


def get_monthly_numbers_dicts_by_date_range():
    """Return monthly financial series dictionaries from PostgreSQL for UI dates."""
    start_date, end_date = get_required_date_range()
    df = fetch_monthly_numbers_from_postgresql(start_date, end_date)
    return {
        'monthly_disposal_cost': dict(zip(df['year_month'], df['monthly_disposal_cost'])),
        'quickbooks_monthly_expenses': dict(zip(df['year_month'], df['quickbooks_monthly_expenses'])),
        'monthly_sales': dict(zip(df['year_month'], df['monthly_sales'])),
        'monthly_payroll': dict(zip(df['year_month'], df['monthly_payroll'])),
    }


def get_operating_cost_metrics(monthly_data):
    """Build daily/monthly/yearly operating-cost metrics from DB monthly data."""
    payroll_values = list(monthly_data['monthly_payroll'].values())
    expense_values = list(monthly_data['quickbooks_monthly_expenses'].values())

    monthly_payroll_avg = statistics.mean(payroll_values)
    monthly_expenses_avg = statistics.mean(expense_values)
    yearly_payroll_total = sum(payroll_values)
    yearly_expenses_total = sum(expense_values)

    daily_payroll = monthly_payroll_avg / WORK_DAYS_IN_MONTH
    daily_expenses = monthly_expenses_avg / WORK_DAYS_IN_MONTH
    daily_operating_cost = daily_payroll + daily_expenses

    if NUM_EMPLOYEES > 0:
        daily_operating_cost_per_employee = daily_operating_cost / NUM_EMPLOYEES
        hourly_rate = round(
            daily_operating_cost_per_employee / DAILY_WORK_HOURS * PROFIT_MARGIN,
            2,
        )
    else:
        daily_operating_cost_per_employee = 0.0
        hourly_rate = 0.0

    return {
        'daily_payroll': round(daily_payroll, 2),
        'daily_operating_cost': round(daily_operating_cost, 2),
        'daily_operating_cost_per_employee': round(daily_operating_cost_per_employee, 2),
        'hourly_rate': hourly_rate,
        'monthly_payroll_avg': round(monthly_payroll_avg, 2),
        'monthly_expenses_avg': round(monthly_expenses_avg, 2),
        'monthly_operating_cost_avg': round(monthly_payroll_avg + monthly_expenses_avg, 2),
        'yearly_payroll_total': round(yearly_payroll_total, 2),
        'yearly_expenses_total': round(yearly_expenses_total, 2),
        'yearly_operating_cost_total': round(yearly_payroll_total + yearly_expenses_total, 2),
    }

def get_required_date_range():
    """Read and validate start/end dates from the UI and return both values."""
    start_date = start_date_entry.get().strip()
    end_date = end_date_entry.get().strip()

    if not start_date or not end_date:
        raise ValueError("Please enter both start and end dates in YYYY-MM format.")

    datetime.strptime(start_date, '%Y-%m')
    datetime.strptime(end_date, '%Y-%m')
    return start_date, end_date


def get_number_of_months_from_date_range():
    """Return inclusive month count for the validated UI start/end date range."""
    start_date, end_date = get_required_date_range()
    start = datetime.strptime(start_date, '%Y-%m')
    end = datetime.strptime(end_date, '%Y-%m')

    if end < start:
        raise ValueError("End date must be on or after the start date.")

    return ((end.year - start.year) * 12) + (end.month - start.month) + 1

def fetch_equipment_values():
    """Fetch equipment name and purchase price."""
    equipment_values = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT equipment_name, purchase_price FROM equipment;"
            )
            rows = cur.fetchall()

    for row in rows:
        if len(row) < 2 or row[0] is None or row[1] is None:
            continue
        equipment_values[str(row[0])] = float(row[1])

    return equipment_values

# ========================================================================== #
# ======================= Machine Learning with Matplot ==================== #
# ========================================================================== #
def predict_and_plot_with_matplot(data_dict, column_name, future_months=3):
    """
    Makes a prediction for the specified number of future months for 
    Quickbooks expenses, Monthly Payroll, and Disposal cost using the 
    Prophet model.
    
    Parameters:
    data_dict (dict): Dictionary containing historical data.
    column_name (str): Name of the column to be used in the plot.
    future_months (int): Number of future months to predict. Default is 3.
    
    Returns:
    None
    """
    # Prepare the data
    data = pd.DataFrame(list(data_dict.items()), columns=['ds', 'y'])
    data['ds'] = pd.to_datetime(data['ds'])

    # Filter the data to only include the last twelve months
    data = data.tail(12)

    # Initialize the Prophet model
    model = Prophet()
    model.fit(data)

    # Create a dataframe for future dates
    future = model.make_future_dataframe(periods=future_months, freq='ME')
    
    # Predict the future values
    forecast = model.predict(future)

    # Plot the results
    plt.figure(figsize=(10, 5))

    # Plot the previous data (last twelve months)
    plt.plot(data['ds'], data['y'], 'bo-', label='Previous Data')

    # Plot predicted data (next three months)
    plt.plot(forecast['ds'], forecast['yhat'], 'ro--', label="Predicted Data")

    # Add labels and title
    plt.xlabel('Month')
    plt.ylabel(column_name)
    plt.title(f"{column_name}, For Past 12 Months and Predicted Next 3 Months")
    
    # Format the x-axis labels
    plt.gca().xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mpl.dates.MonthLocator(interval=1))
    plt.gcf().autofmt_xdate()

    # Add legend
    plt.legend()

    # Implement mplcurors for interactive tooltips
    cursor = mplcursors.cursor(hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(f"{sel.target[1]:,.0f}"))

    # Adjust layout to prevent x-axis labels from going off bottom of the screen
    plt.tight_layout()

    # Show plot
    plt.show()

# ========================================================================== #
# ======================== Machine Learning using Plotly =================== #
# ========================================================================== #
def predict_and_plot_with_plotly(data_dicts, column_names, future_months=3):
    """
    Makes a prediction for the specified number of future months for 
    Quickbooks expenses, Monthly Payroll, and Disposal cost using the 
    Prophet model and plots the results using Plotly.
    
    Parameters:
    data_dicts (list of dict): List of dictionaries containing historical data.
    column_names (list of str): List of column names to be used in the plot.
    future_months (int): Number of future months to predict. Default is 3.
    
    Returns:
    None
    """
    # fig = make_subplots(rows=3, cols=1, shared_xaxes=False, 
    #                     vertical_spacing=0.1, subplot_titles=column_names)
    fig = make_subplots(rows=len(data_dicts), cols=1, shared_xaxes=False, 
                        vertical_spacing=0.1, subplot_titles=column_names)

    for i, (data_dict, column_name) in enumerate(zip(data_dicts, column_names), 
                                                 start=1):
        # Prepare the data
        data = pd.DataFrame(list(data_dict.items()), columns=['ds', 'y'])
        data['ds'] = pd.to_datetime(data['ds'])

        # Initialize the Prophet model
        model = Prophet()
        model.fit(data)

        # Create a dataframe for future dates
        future = model.make_future_dataframe(periods=future_months, freq='ME')
        
        # Predict the future values
        forecast = model.predict(future)

        # Add previous data to the subplot
        fig.add_trace(go.Scatter(x=data['ds'], y=data['y'], mode='lines+markers', 
                                 name=f'Previous Data - {column_name}'), 
                                 row=i, col=1)

        # Add predicted data to the subplot
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], 
                                 mode='lines+markers', 
                                 name=f'Predicted Data - {column_name}',
                                 line=dict(dash='dashdot')),
                                 row=i, col=1)

    # Update layout
    fig.update_layout(height=1000, width=2000, 
                      title_text="Predictions for Monthly Expenses, "
                      "Payroll, Sales and Disposal Cost",
                      title_x=0.5,)
    fig.update_xaxes(title_text="Month", tickformat='%Y-%m')
    fig.update_yaxes(title_text="Values")

    # Show plot
    fig.show()

# ========================================================================== #
# =========================== Calculate Financials ========================= #
# ========================================================================== #
def display_financials(title, financials):
    """
    Helper function to display financial metrics.
    
    Parameters:
    title (str): The title of the financial section.
    financials (dict): Dictionary containing financial metrics to display.
    
    Returns:
    None
    """
    print("\n")
    print(title.center(20, "-"))
    for key, value in financials.items():
        print(f"{key} = {value:,.2f}")


def calculate_financials():
    """
    Calculate and display various financial metrics based on the selected option.
    
    Returns: 
        None
    """
    try:
        option = options.get()
        monthly_data_options = {"Daily", "Monthly", "Yearly", "Disposal", "Quickbooks", "Sales"}
        monthly_data = None
        operating_cost_metrics = None

        if option in monthly_data_options:
            monthly_data = get_monthly_numbers_dicts_by_date_range()
            operating_cost_metrics = get_operating_cost_metrics(monthly_data)

        if option == "Daily":
            financials = {
                "Daily Operating Cost": operating_cost_metrics['daily_operating_cost'],
                "Daily Operating Cost per Employee": operating_cost_metrics['daily_operating_cost_per_employee'],
                "Total daily payroll": operating_cost_metrics['daily_payroll'],
                "Rate per Hour": operating_cost_metrics['hourly_rate'],
            }
            display_financials("Daily", financials)

        elif option == "Monthly":
            financials = {
                "Average monthly payroll": operating_cost_metrics['monthly_payroll_avg'],
                "Average monthly expenses": operating_cost_metrics['monthly_expenses_avg'],
                "Average monthly operating cost": operating_cost_metrics['monthly_operating_cost_avg'],
            }
            display_financials("Monthly", financials)

        elif option == "Yearly":
            financials = {
                "Total payroll for date range": operating_cost_metrics['yearly_payroll_total'],
                "Total expenses for date range": operating_cost_metrics['yearly_expenses_total'],
                "Total operating cost for date range": operating_cost_metrics['yearly_operating_cost_total'],
            }
            display_financials("Yearly", financials)

        elif option == "Equipment":
            equipment_values = fetch_equipment_values()

            if not equipment_values:
                messagebox.showwarning(
                    "No Results",
                    "No equipment data was returned from the equipment table.",
                )
                return
            
            print("\n")
            print("Equipment".center(20, "-"))
            for e, v in equipment_values.items():
                print(f"{e}: ${v:,.2f}")
            total_equipment = round(sum(equipment_values.values()))
            avg_equipment_cost = statistics.mean(equipment_values.values())
            financials = {
                "Total cost of all equipment": total_equipment,
                "Average equipment cost": avg_equipment_cost
            }
            display_financials("Equipment", financials)

        elif option == "Disposal":
            monthly_disposal_cost = monthly_data['monthly_disposal_cost']
            total_disposal_cost = sum(monthly_disposal_cost.values())
            avg_disposal_cost = round(statistics.mean(monthly_disposal_cost.values())) 
            avg_daily_disposal_cost = round(avg_disposal_cost / WORK_DAYS_IN_MONTH)  
            financials = {
                "Total disposal cost": total_disposal_cost,
                "The average monthly disposal cost": avg_disposal_cost,
                "The average daily disposal cost": avg_daily_disposal_cost,
            }
            display_financials("Disposal", financials)

        elif option == "Revenue":
            total_revenue = sum([year_data["revenue"] for year_data in revenue.values()])
            total_net_profit = sum([year_data["net profit"] for year_data in revenue.values()])
            num_employees = NUM_EMPLOYEES
            num_years = len(revenue)
            avg_revenue = round(total_revenue / num_years, 2)
            avg_net_profit = round(total_net_profit / num_years, 2)
            avg_net_profit_per_employee = round(avg_net_profit / num_employees, 2) if num_employees != 0 else 0
            avg_profit_margin = round(avg_net_profit / avg_revenue, 2) if avg_revenue != 0 else 0
            avg_revenue_per_employee = round(avg_revenue / num_employees, 2) if num_employees != 0 else 0
            financials = {
                "Total revenue": total_revenue,
                "Total net profit": total_net_profit,
                "Average revenue": avg_revenue,                
                "Average revenue per employee": avg_revenue_per_employee,
                "Average net profit": avg_net_profit,
                "Average net profit per employee": avg_net_profit_per_employee,
                "Average profit margin": avg_profit_margin,
            }
            display_financials("Revenue", financials)

        elif option == "Quickbooks":
            quickbooks_monthly_expenses = monthly_data['quickbooks_monthly_expenses']
            total_qb_monthly_expenses = round(sum(quickbooks_monthly_expenses.values()), 2)
            avg_qb_monthly_expenses = round(statistics.mean(quickbooks_monthly_expenses.values()), 2)
            financials = {
            "Total quickbooks monthly expenses": total_qb_monthly_expenses,
            "Average quickbooks monthly expense": avg_qb_monthly_expenses,
            }
            display_financials("Quickbooks", financials)

        elif option == "Sales":
            monthly_sales = monthly_data['monthly_sales']
            total_monthly_sales = round(sum(monthly_sales.values()), 2)
            avg_monthly_sales = round(statistics.mean(monthly_sales.values()), 2)
            financials = {
                "Total monthly sales": total_monthly_sales,
                "Average monthly sales": avg_monthly_sales,
            }
            display_financials("Sales", financials)

        else:
            messagebox.showwarning("No Results", "Please choose a valid option.")

    except Exception:
        logger.exception("Failed to calculate financial metrics")
        messagebox.showerror(
            "Financials Error",
            "Unable to calculate financial results right now. Please verify inputs and database connectivity.",
        )

# ========================================================================== #
# ============================== Display Chart ============================= #
# ========================================================================== #
def plot_pie_chart(title, labels, sizes):
    """
    Helper function to plot a pie chart.
    
    Parameters:
    title (str): The title of the pie chart.
    labels (list): The labels for the pie chart.
    sizes (list): The sizes for the pie chart.
    
    Returns:
    None
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, autopct='%.1f%%')
    ax.set_title(title, fontsize=18)
    ax.axis('equal')
    plt.show()


def plot_bar_chart(title, labels, values, number_of_months=13):
    """
    Helper function to plot a bar chart.
    
    Parameters:
    title (str): The title of the bar chart.
    labels (list): The labels for the bar chart.
    values (list): The values for the bar chart.
    
    Returns:
    None
    """
    # Show only the past number of months
    labels = labels[-number_of_months:]
    values = values[-number_of_months:]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, values)
    ax.set_title(title, fontsize=18)
    ax.set_xlabel('Month')
    ax.set_ylabel('Values')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Add horizontal gridlines
    ax.grid(axis='y', linewidth=0.25)

    # Add mplcursors tooltips
    cursor = mplcursors.cursor(bars, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(f'{labels[sel.index]}: {values[sel.index]:,.2f}'))

    plt.show()


def plot_line_chart(title, x, y1, y2, label1, label2):
    """
    Helper function to plot a line chart with two lines.
    
    Parameters:
    title (str): The title of the line chart.
    x (list): The x-axis values for the line chart.
    y1 (list): The y-axis values for the first line.
    y2 (list): The y-axis values for the second line.
    label1 (str): The label for the first line.
    label2 (str): The label for the second line.
    
    Returns:
    None
    """
    # Calculate percent profit
    percent_profit = [(net / rev) * 100 if rev != 0 else 0 for net, rev in zip(y2, y1)]

    # Round the values to the nearest two digits
    y1 = [round(value, 2) for value in y1]
    y2 = [round(value, 2) for value in y2]
    percent_profit = [round(value, 2) for value in percent_profit]

    # Format the 'Revenue' and 'Net Profit' values
    y1_formatted = [f'{value:,.2f}' for value in y1]
    y2_formatted = [f'{value:,.2f}' for value in y2]
    percent_profit_formatted = [f'{value:.2f}%' for value in percent_profit]

    fig, ax = plt.subplots(figsize=(10, 5))
    line1, = ax.plot(x, y1, 'o-', label=label1)
    line2, = ax.plot(x, y2, 'o-', label=label2)
    ax.set_title(title, fontsize=18)
    # ax.set_xlabel('Year')
    ax.set_ylabel('Values')
    ax.grid(axis='y', linewidth=0.25)
    # plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # Add mplcursors tooltips
    cursor1 = mplcursors.cursor(line1, hover=True)
    cursor1.connect("add", lambda sel: sel.annotation.set_text(f'{x[int(sel.index)]}: {y1[int(sel.index)]:,.2f}'))

    cursor2 = mplcursors.cursor(line2, hover=True)
    cursor2.connect("add", lambda sel: sel.annotation.set_text(
        f'{x[int(sel.index)]}: {y2[int(sel.index)]:,.2f}\nPercent Profit: {percent_profit[int(sel.index)]:.2f}%'))

    # Create a table at the bottom of the plot
    table_data = {
        'Year': x,
        'Revenue': y1_formatted,
        'Net Profit': y2_formatted,
        'Percent Profit (%)': percent_profit_formatted
    }
    table_df = pd.DataFrame(table_data)
    table_df = table_df.set_index('Year').transpose()
    table = plt.table(cellText=table_df.values,
                      rowLabels=table_df.index,
                      colLabels=table_df.columns,
                      cellLoc='center',
                      loc='bottom',
                      bbox=[0, -0.3, 1, 0.2])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    plt.subplots_adjust(left=0.1, bottom=0.3)
    plt.tight_layout()

    plt.show()


def display_chart():
    """
    Displays various charts based on the selected option.

    The function retrieves the selected option from the 'options' object and
    displays a corresponding chart using matplotlib. If an invalid
    option is selected, a warning message is displayed. The available options and
    their respective charts are:

    - 'Monthly': Displays a pie chart of monthly expenses including Payroll, 
    Expenses, and Average Fuel Cost.
    - 'Yearly': Displays a pie chart of yearly expenses including Payroll, Expenses,
    and Average Fuel Cost.
    - 'Trucks': Displays a pie chart of truck values.
    - 'Equipment': Displays a pie chart of equipment values.
    - 'Disposal': Displays a bar chart of disposal costs for the past 12 months.
    - 'Quickbooks': Displays a bar chart of Quickbooks expenses for the past 12 months.
    - 'Predictions(Matplot)': Predicts and plots data for various categories using Matplotlib.
    - 'Predictions(Plotly)': Predicts and plots data for various categories using Plotly.

    Each chart is displayed in a new figure window with appropriate titles and
    labels. 
    """
    try:
        option = options.get()
        monthly_data_options = {
            'Monthly', 'Yearly', 'Disposal', 'Quickbooks', 'Sales',
            'Predictions(Matplot)', 'Predictions(Plotly)'
        }
        monthly_data = None
        operating_cost_metrics = None

        if option in monthly_data_options:
            monthly_data = get_monthly_numbers_dicts_by_date_range()
            operating_cost_metrics = get_operating_cost_metrics(monthly_data)

        if option == 'Monthly':
            labels = ['Payroll', 'Expenses']
            sizes = [
                operating_cost_metrics['monthly_payroll_avg'],
                operating_cost_metrics['monthly_expenses_avg'],
            ]
            plot_pie_chart("TDC Monthly Expenses", labels, sizes)

        elif option == 'Yearly':
            labels = ['Payroll', 'Expenses']
            sizes = [
                operating_cost_metrics['yearly_payroll_total'],
                operating_cost_metrics['yearly_expenses_total'],
            ]
            plot_pie_chart("TDC Yearly Expenses", labels, sizes)

        elif option == "Equipment":
            equipment_values = fetch_equipment_values()

            if not equipment_values:
                messagebox.showwarning(
                    "No Results",
                    "No truck data was returned from the trucks table.",
                )
                return

            labels = list(equipment_values.keys())
            values = list(equipment_values.values())
            plot_pie_chart("Equipment Values", labels, values)

        elif option == 'Disposal':
            start_date, end_date = get_required_date_range()

            monthly_disposal_cost = monthly_data['monthly_disposal_cost']
            labels = list(monthly_disposal_cost.keys())
            values = list(monthly_disposal_cost.values())
            plot_bar_chart(f"Disposal Costs from {start_date} to {end_date}", 
                           labels, 
                           values,
                           len(monthly_disposal_cost))

        elif option == 'Revenue':
            labels = list(revenue.keys())
            total_revenue = [revenue[year]["revenue"] for year in revenue]
            net_profit = [revenue[year]["net profit"] for year in revenue]
            plot_line_chart("Revenue and Net Profit by Year", labels, 
                            total_revenue, net_profit, "Total Revenue", 
                            "Net Profit")

        elif option == 'Quickbooks':
            start_date, end_date = get_required_date_range()

            quickbooks_monthly_expenses = monthly_data['quickbooks_monthly_expenses']
            labels = list(quickbooks_monthly_expenses.keys())
            values = list(quickbooks_monthly_expenses.values())
            plot_bar_chart(f"Quickbooks Expenses from {start_date} to {end_date}", 
                           labels, 
                           values,
                           len(quickbooks_monthly_expenses))

        elif option == 'Sales':
            start_date, end_date = get_required_date_range()

            monthly_sales = monthly_data['monthly_sales']
            labels = list(monthly_sales.keys())
            values = list(monthly_sales.values())
            plot_bar_chart(f"Monthly Sales from {start_date} to {end_date}", 
                           labels, 
                           values,
                           len(monthly_sales))

        elif option == 'Predictions(Matplot)':
            quickbooks_monthly_expenses = monthly_data['quickbooks_monthly_expenses']
            monthly_payroll = monthly_data['monthly_payroll']
            monthly_disposal_cost = monthly_data['monthly_disposal_cost']
            monthly_sales = monthly_data['monthly_sales']
            # Predict and plot for each dictionary
            predict_and_plot_with_matplot(quickbooks_monthly_expenses, 
                                          'Quickbooks Monthly Expenses')
            predict_and_plot_with_matplot(monthly_payroll, 
                                          'Monthly Payroll')
            predict_and_plot_with_matplot(monthly_disposal_cost, 
                                          'Monthly Disposal Cost')
            predict_and_plot_with_matplot(monthly_sales,
                                          'Monthly Sales')

        elif option == 'Predictions(Plotly)':
            quickbooks_monthly_expenses = monthly_data['quickbooks_monthly_expenses']
            monthly_payroll = monthly_data['monthly_payroll']
            monthly_disposal_cost = monthly_data['monthly_disposal_cost']
            monthly_sales = monthly_data['monthly_sales']
            # Predict and plot for each dictionary
            data_dicts = [quickbooks_monthly_expenses, monthly_payroll, 
                          monthly_disposal_cost, monthly_sales]
            column_names = ['Quickbooks Monthly Expenses', 'Monthly Payroll', 
                            'Monthly Disposal Cost', 'Monthly Sales']
            predict_and_plot_with_plotly(data_dicts, column_names)

        else:
            messagebox.showwarning("No Results", 
                    "Sorry, we do not have a chart for that option to display.")
            
    except Exception:
        logger.exception("Failed to generate chart")
        messagebox.showerror(
            "Chart Error",
            "Unable to generate the selected chart right now. Please verify inputs and database connectivity.",
        )


# ========================================================================== #
# ============================== Tkinter GUI =============================== #
# ========================================================================== #
if __name__=="__main__":
    root = tk.Tk()
    root.minsize(width=100, height=100)
    root.title("Financials")
    root.config(padx=25, pady=25)

    start_date_label = tk.Label(root, text="Start Date YYYY-MM")
    start_date_label.grid(column=1, row=0, padx=5, pady=5)
    start_date_entry = tk.Entry(root, width=20)
    start_date_entry.grid(column=1, row=1, padx=5, pady=10)

    end_date_label = tk.Label(root, text="End Date YYYY-MM")
    end_date_label.grid(column=2, row=0, padx=5, pady=5)
    end_date_entry = tk.Entry(root, width=20)
    end_date_entry.grid(column=2, row=1, padx=5, pady=10)

    options = ttk.Combobox(root, state="readonly", 
                            values=[
                                "Daily", 
                                "Monthly", 
                                "Yearly", 
                                "Trucks", 
                                "Equipment", 
                                "Disposal",
                                "Revenue",
                                "Quickbooks",
                                "Sales",
                                "Predictions(Matplot)",
                                "Predictions(Plotly)",
                                    ]
                                )

    options.grid(column=1, row=2, padx=5, pady=10)
    options_label = tk.Label(text="Options")
    options_label.grid(column=2, row=2, padx=5, pady=10)

    calculate_button = ttk.Button(root, text="Calculate", command=calculate_financials)
    calculate_button.grid(column=1, row=3, padx=5, pady=5)

    chart_button = ttk.Button(root, text="Display Chart", command=display_chart)
    chart_button.grid(column=2, row=3, padx=5, pady=5)


    root.mainloop()

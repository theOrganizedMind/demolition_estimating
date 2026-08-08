import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext, font
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import datetime
from idlelib.tooltip import Hovertip
import logging

from postgresql import get_db_connection

# ========================================================================== #
# ================================== INFO ================================== #
# ========================================================================== #

# ========================================================================== #
# ================================== TODO ================================== #
# ========================================================================== #
# TODO: 
# Add PostgreSQL variables to .env before running program. 
# See postgresql.py for required parameters.
# ========================================================================== #

todays_date = datetime.now().strftime("%m%d%Y")

# =========================================================================== #
# ======================== Get Data from PostgreSQL ========================= #
# =========================================================================== #

def fetch_data_from_postgresql():
    """Fetch project data from PostgreSQL and shape it for model training."""
    query = """
        SELECT
            job_number AS "Job Number",
            awarded_date AS "Awarded Date",
            project_description AS "Description",
            structure_type AS "Structure Type",
            sqft AS "SqFt",
            bid_price AS "Bid Price",
            job_cost AS "Job Cost",
            estimator AS "Estimator"
        FROM project;
    """

    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)

    if df.empty:
        messagebox.showwarning(
            "No Project Data",
            "No project rows were returned from PostgreSQL table 'project'.",
        )
        return df

    df['SqFt'] = pd.to_numeric(df['SqFt'], errors='coerce')
    df['Bid Price'] = pd.to_numeric(df['Bid Price'], errors='coerce')
    df['Job Cost'] = pd.to_numeric(df['Job Cost'], errors='coerce')
    df['Awarded Date'] = pd.to_datetime(df['Awarded Date'], errors='coerce')

    # Drop rows with missing model-critical values to keep downstream training stable.
    df = df.dropna(subset=['Job Number', 'Description', 'Structure Type', 'SqFt', 'Bid Price', 'Job Cost'])
    df['SqFt'] = df['SqFt'].astype(int)
    df['Profit and Loss %'] = round(((df['Bid Price'] - df['Job Cost']) / df['Bid Price']) * 100, 2)
    df = df.set_index('Job Number')

    print("\nData from PostgreSQL")
    print("\nDataframe with 'Profit and Loss %' column:")
    print(df.tail())
    return df

# ===========================================================================
# ======================= New Estimate costs using models ===================
# ===========================================================================
def train_models(df):
    """
     Train two tuned ML model families for bid and cost prediction.

     Models:
     - Ridge Regression: regularized linear baseline.
     - Random Forest: non-linear ensemble with constraints to reduce overfitting.

     Both models use cross-validation and hyperparameter tuning.

    Parameters:
    df (DataFrame): The input DataFrame containing the features and target variables.

        Returns:
        tuple: Tuned estimators, holdout sets, and CV summary values.
    """
    X = df[['Description', 'Structure Type', 'SqFt']]
    y_bid = df['Bid Price']
    y_cost = df['Job Cost']

    # Split the data into training and testing sets
    X_train, X_test, y_bid_train, y_bid_test, y_cost_train, y_cost_test = \
        train_test_split(X, y_bid, y_cost, test_size=0.2, random_state=42)
    
    # Define the column transformer for one-hot encoding
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(), ['Description', 'Structure Type']),
            ('num', StandardScaler(), ['SqFt'])
        ])

    # Use a dynamic CV split count so this also works with smaller datasets.
    cv_splits = min(5, max(2, len(X_train) // 4))
    cv_strategy = KFold(n_splits=cv_splits, shuffle=True, random_state=42)

    # Ridge (regularized linear model) with CV tuning.
    ridge_bid_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', Ridge())
    ])
    ridge_cost_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', Ridge())
    ])
    ridge_params = {
        'model__alpha': [0.01, 0.1, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0]
    }

    ridge_bid_search = GridSearchCV(
        ridge_bid_pipeline,
        ridge_params,
        cv=cv_strategy,
        scoring='neg_mean_absolute_error',
        n_jobs=1,
    )
    ridge_bid_search.fit(X_train, y_bid_train)

    ridge_cost_search = GridSearchCV(
        ridge_cost_pipeline,
        ridge_params,
        cv=cv_strategy,
        scoring='neg_mean_absolute_error',
        n_jobs=1,
    )
    ridge_cost_search.fit(X_train, y_cost_train)

    # Random Forest with conservative defaults and CV tuning to reduce overfitting.
    rf_bid_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(random_state=42, n_jobs=1))
    ])
    rf_cost_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(random_state=42, n_jobs=1))
    ])
    rf_params = {
        'model__n_estimators': [200, 350, 500],
        'model__max_depth': [5, 8, 12, None],
        'model__min_samples_split': [2, 4, 6, 10],
        'model__min_samples_leaf': [1, 2, 4],
        'model__max_features': ['sqrt', 0.7, 1.0],
        'model__bootstrap': [True]
    }

    rf_bid_search = RandomizedSearchCV(
        rf_bid_pipeline,
        rf_params,
        n_iter=15,
        cv=cv_strategy,
        scoring='neg_mean_absolute_error',
        n_jobs=1,
        random_state=42,
    )
    rf_bid_search.fit(X_train, y_bid_train)

    rf_cost_search = RandomizedSearchCV(
        rf_cost_pipeline,
        rf_params,
        n_iter=15,
        cv=cv_strategy,
        scoring='neg_mean_absolute_error',
        n_jobs=1,
        random_state=42,
    )
    rf_cost_search.fit(X_train, y_cost_train)

    cv_results = {
        'cv_splits': cv_splits,
        'ridge_bid_cv_mae': abs(ridge_bid_search.best_score_),
        'ridge_cost_cv_mae': abs(ridge_cost_search.best_score_),
        'rf_bid_cv_mae': abs(rf_bid_search.best_score_),
        'rf_cost_cv_mae': abs(rf_cost_search.best_score_),
        'ridge_bid_best_params': ridge_bid_search.best_params_,
        'ridge_cost_best_params': ridge_cost_search.best_params_,
        'rf_bid_best_params': rf_bid_search.best_params_,
        'rf_cost_best_params': rf_cost_search.best_params_,
    }

    return ridge_bid_search.best_estimator_, ridge_cost_search.best_estimator_, \
        rf_bid_search.best_estimator_, rf_cost_search.best_estimator_, X_test, \
        y_bid_test, y_cost_test, cv_results

# ===========================================================================
# ======================= New Estimate costs using models ===================
# ===========================================================================
def estimate_costs(models, square_feet, description, structure_type):
    """
    Estimate bid prices and job costs using multiple machine learning models.

    Parameters:
    models (list): A list containing trained models in this order:
    [ridge_bid_model, ridge_cost_model, rf_bid_model, rf_cost_model]
    square_feet (float): The square footage of the project.
    description (str): A description of the project(e.g., Building Demo, 
    House Demo, Interior Demolition).
    structure_type (str): The type of structure (e.g., Wood, Metal, Other).

    Returns:
    tuple: A tuple containing four estimated values in this order:
           (ridge_estimated_bid_price, ridge_estimated_job_cost,
            rf_estimated_bid_price, rf_estimated_job_cost)
    """
    ridge_bid_model, ridge_cost_model, rf_bid_model, rf_cost_model = models[:4]
    input_data = pd.DataFrame([[description, structure_type, square_feet]], 
                              columns=['Description', 'Structure Type', 'SqFt'])
    ridge_estimated_bid_price = ridge_bid_model.predict(input_data)[0]
    ridge_estimated_job_cost = ridge_cost_model.predict(input_data)[0]
    rf_estimated_bid_price = rf_bid_model.predict(input_data)[0]
    rf_estimated_job_cost = rf_cost_model.predict(input_data)[0]

    return ridge_estimated_bid_price, ridge_estimated_job_cost, \
        rf_estimated_bid_price, rf_estimated_job_cost

# ===========================================================================
# ======================= New Evaluate model performance ====================
# ===========================================================================
def on_closing_performance_data(root):
    if root:
        root.quit()
        root.destroy()


def show_performance_data(performance_data):
    """
    Display model performance and CV summary text in a GUI window.

    Returns:
    None
    """
    root = Tk()
    root.title("Model Performance Data")

    # Customize font and colors
    custom_font = font.Font(family="Times New Roman", size=12)
    # text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=10,
    #                                       font=custom_font, fg="green", 
    #                                       bg="black")
    text_area = scrolledtext.ScrolledText(root, wrap=WORD, width=40, height=20,
                                          font=custom_font, fg="green")
    text_area.pack(padx=10, pady=10)

    text_area.insert(END, performance_data)

    # Set the protocol for window closing
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing_performance_data(root))

    root.mainloop()

# ===========================================================================
# ======================= New Evaluate model performance ====================
# ===========================================================================
def evaluate_models(models):
    """
    Evaluate the performance of multiple machine learning models on test data 
    and display the results.

    Parameters:
    models (list): A list containing the following elements in order:
        [ridge_bid_model, ridge_cost_model, rf_bid_model, rf_cost_model,
         X_test, y_bid_test, y_cost_test, cv_results]

    Mean Absolute Error (MAE): Tells you the average absolute difference 
    between predicted and actual values. Lower values indicate better 
    performance.

    Mean Squared Error (MSE): Measures the average of the squares of the errors,
    giving more weight to larger errors. Lower values are better. 

    R-squared (R²): Indicates how well the model explains the variance in the data.
    Higher values indicate better performance. Values closer to 1 indicate a better
    fit. 

    Returns:
    None
    """
    ridge_bid_model, ridge_cost_model, rf_bid_model, rf_cost_model, X_test, \
        y_bid_test, y_cost_test, cv_results = models

    # Predictions for Ridge
    y_bid_pred_ridge = ridge_bid_model.predict(X_test)
    y_cost_pred_ridge = ridge_cost_model.predict(X_test)

    # Predictions for Random Forest
    y_bid_pred_rf = rf_bid_model.predict(X_test)
    y_cost_pred_rf = rf_cost_model.predict(X_test)

    # Evaluation for Ridge
    mae_bid_ridge = mean_absolute_error(y_bid_test, y_bid_pred_ridge)
    mse_bid_ridge = mean_squared_error(y_bid_test, y_bid_pred_ridge)
    r2_bid_ridge = r2_score(y_bid_test, y_bid_pred_ridge)

    mae_cost_ridge = mean_absolute_error(y_cost_test, y_cost_pred_ridge)
    mse_cost_ridge = mean_squared_error(y_cost_test, y_cost_pred_ridge)
    r2_cost_ridge = r2_score(y_cost_test, y_cost_pred_ridge)

    # Evaluation for Random Forest
    mae_bid_rf = mean_absolute_error(y_bid_test, y_bid_pred_rf)
    mse_bid_rf = mean_squared_error(y_bid_test, y_bid_pred_rf)
    r2_bid_rf = r2_score(y_bid_test, y_bid_pred_rf)

    mae_cost_rf = mean_absolute_error(y_cost_test, y_cost_pred_rf)
    mse_cost_rf = mean_squared_error(y_cost_test, y_cost_pred_rf)
    r2_cost_rf = r2_score(y_cost_test, y_cost_pred_rf)

    # Positive value indicates test error is worse than CV error.
    ridge_bid_overfit_gap = mae_bid_ridge - cv_results['ridge_bid_cv_mae']
    ridge_cost_overfit_gap = mae_cost_ridge - cv_results['ridge_cost_cv_mae']
    rf_bid_overfit_gap = mae_bid_rf - cv_results['rf_bid_cv_mae']
    rf_cost_overfit_gap = mae_cost_rf - cv_results['rf_cost_cv_mae']

    logging.info("----- Model Performance Data -----")
    logging.info("Ridge - Bid Price:")
    logging.info(f"MAE: {mae_bid_ridge:,.2f} | MSE: {mse_bid_ridge:,.2f} | R²: {r2_bid_ridge:,.2f}")
    logging.info("Ridge - Job Cost:")
    logging.info(f"MAE: {mae_cost_ridge:,.2f} | MSE: {mse_cost_ridge:,.2f} | R²: {r2_cost_ridge:,.2f}")
    logging.info("Random Forest - Bid Price:")
    logging.info(f"MAE: {mae_bid_rf:,.2f} | MSE: {mse_bid_rf:,.2f} | R²: {r2_bid_rf:,.2f}")
    logging.info("Random Forest - Job Cost:")
    logging.info(f"MAE: {mae_cost_rf:,.2f} | MSE: {mse_cost_rf:,.2f} | R²: {r2_cost_rf:,.2f}")

    performance_data = (
        "Cross-Validation:\n"
        f"CV folds: {cv_results['cv_splits']}\n"
        f"Ridge Bid CV MAE: {cv_results['ridge_bid_cv_mae']:,.2f}\n"
        f"Ridge Cost CV MAE: {cv_results['ridge_cost_cv_mae']:,.2f}\n"
        f"RF Bid CV MAE: {cv_results['rf_bid_cv_mae']:,.2f}\n"
        f"RF Cost CV MAE: {cv_results['rf_cost_cv_mae']:,.2f}\n\n"
        "Holdout Test Performance:\n"
        f"Ridge Bid: MAE {mae_bid_ridge:,.2f}\n"
        f"MSE {mse_bid_ridge:,.2f}\n"
        f"R² {r2_bid_ridge:,.2f}\n"
        f"Overfit Gap(MAE): {ridge_bid_overfit_gap:,.2f}\n"
        f"Ridge Cost: MAE {mae_cost_ridge:,.2f}\n" 
        f"MSE {mse_cost_ridge:,.2f}\n"
        f"R² {r2_cost_ridge:,.2f}\n" 
        f"Overfit Gap(MAE): {ridge_cost_overfit_gap:,.2f}\n"
        f"RF Bid: MAE {mae_bid_rf:,.2f}\n" 
        f"MSE {mse_bid_rf:,.2f}\n"
        f"R² {r2_bid_rf:,.2f}\n" 
        f"Overfit Gap(MAE): {rf_bid_overfit_gap:,.2f}\n"
        f"RF Cost: MAE {mae_cost_rf:,.2f}\n" 
        f"MSE {mse_cost_rf:,.2f}\n" 
        f"R² {r2_cost_rf:,.2f}\n" 
        f"Overfit Gap(MAE): {rf_cost_overfit_gap:,.2f}\n\n"
        "Best Hyperparameters:\n"
        f"Ridge Bid: {cv_results['ridge_bid_best_params']}\n"
        f"Ridge Cost: {cv_results['ridge_cost_best_params']}\n"
        f"RF Bid: {cv_results['rf_bid_best_params']}\n"
        f"RF Cost: {cv_results['rf_cost_best_params']}\n"
    )

    show_performance_data(performance_data)

# ===========================================================================
# ========================== Main Program =================================== 
# ===========================================================================
def on_closing_estimates(info):
    if info:
        info.quit()
        info.destroy()


def create_tooltip(widget, text):
    """Creates tooltips for the tkinter launch_demo_window widgets"""
    Hovertip(widget, text, hover_delay=500)

# ===========================================================================
# ========================== New Show Estimates ============================= 
# ===========================================================================
def show_estimates(average_bid_price, average_job_cost, 
                   ridge_estimated_bid_price, ridge_estimated_job_cost, 
                   rf_estimated_bid_price, rf_estimated_job_cost):
    """
    Displays a window with various estimate details for a demolition project.

    Parameters:
    average_bid_price (float): The average bid price for similar projects.
    average_job_cost (float): The average job cost for similar projects.
    ridge_estimated_bid_price (float): The bid price estimated using Ridge.
    ridge_estimated_job_cost (float): The job cost estimated using Ridge.
    rf_estimated_bid_price (float): The bid price estimated using Random Forest.
    rf_estimated_job_cost (float): The job cost estimated using Random Forest.

    Description:
    This function creates a new Tkinter window titled "Estimates" and displays
    the provided estimate details in a scrollable text area. The window is 
    customized with a specific font and color for better readability.

    The function also sets a protocol to handle the window closing event.
    """
    global description
    info = Tk()
    info.title("Estimates")

    # Customize font and colors
    custom_font = font.Font(family="Times New Roman", size=12)
    text_area = scrolledtext.ScrolledText(info, wrap=WORD, width=40, height=20,
                                          font=custom_font, fg="green")
    text_area.pack(padx=10, pady=10)

    avg_per_profit = round(int(average_bid_price - average_job_cost)\
         / average_bid_price * 100, 2)
    ridge_per_profit = round(int(ridge_estimated_bid_price - ridge_estimated_job_cost)\
        / ridge_estimated_bid_price * 100, 2)
    rf_per_profit = round(int(rf_estimated_bid_price - rf_estimated_job_cost)\
        / rf_estimated_bid_price * 100, 2)

    estimates = (
        f"{description.get()} Estimates:\n\n"
            "Historical Data:\n"     
            f"Average Bid Price: ${average_bid_price:,.2f}\n"
            f"Average Job Cost: ${average_job_cost:,.2f}\n"
            f"Average % Profit: {avg_per_profit}%\n\n"
            "Machine Learning Models:\n"
            f"Ridge Bid Price: ${ridge_estimated_bid_price:,.2f}\n"
            f"Ridge Job Cost: ${ridge_estimated_job_cost:,.2f}\n"
            f"Ridge % Profit: {ridge_per_profit}%\n\n"
            f"RF Bid Price: ${rf_estimated_bid_price:,.2f}\n"
            f"RF Job Cost: ${rf_estimated_job_cost:,.2f}\n"
            f"RF % Profit: {rf_per_profit}%\n"
        )
    
    text_area.insert(END, estimates)

    # Set the protocol for window closing
    info.protocol("WM_DELETE_WINDOW", lambda: on_closing_estimates(info))

    info.mainloop()

# ============================================================================ #
# ============================== New Estimate Button ========================= #
# ============================================================================ #
def estimate_button():
        """
        Handles the estimation process based on user input and selected 
        description.

        This function retrieves user input values for description, square footage,
        lower limit, and upper limit. It the filters the project data based on 
        these inputs and calculates average job cost and bid price. Depending
        on the selected description, it either launches a demo estimating window 
        for further input and directly displays the estimates. Additionally, it 
        generates a bar chart of the most recent projects and a line chart
        displaying the trend of the projects overtime.

        Global Variables:
            description (ttk.Combobox): The description of the project.
            lower_limit_input (tk.Entry): The lower limit of square footage.
            upper_limit_input (tk.Entry): The upper limit of square footage.
            sqft_input (tk.Entry): The total square footage.
            df (pd.Dataframe): The Dataframe containing project data.
            models (dict): The dictionary containing estimation models.

        Raises: ValueError: If the user input for square footage or limits
            is not a valid integer.

        Displays:
            - Error message if the input values are invalid.
            - Warning message if no data is found for the selected project type.
            - Estimates using linear regression and random forest models.
            - A new window for estimating projects based on description.
            - A bar chart of the most recent projects.
            - A line chart showing the trend of projects overtime.
        """
        global description, lower_limit_input, upper_limit_input, sqft_input, \
        df, models, structure_type

        try:
            description_value = description.get()
            sqft_value = int(sqft_input.get())
            structure_value = structure_type.get()
            lower_limit_value = int(lower_limit_input.get())
            upper_limit_value = int(upper_limit_input.get())
        except ValueError:
            messagebox.showerror("Invalid Input", 
                    "Please enter valid numbers for square footage and limits.")
            return

        if description_value in ["Building Demo", "House Demo"]:
            projects = df.loc[(df["Description"] == description_value) & \
                              (df['Structure Type'] == structure_value) & \
                        (df["SqFt"].between(lower_limit_value, upper_limit_value))]
        else:
            projects = df.loc[(df["Description"] == description_value) & \
                        (df["SqFt"].between(lower_limit_value, upper_limit_value))]

        if not projects.empty:
            average_job_cost = round(projects["Job Cost"].mean())
            average_bid_price = round(projects["Bid Price"].mean())

            ridge_estimated_bid_price, ridge_estimated_job_cost, rf_estimated_bid_price, \
                rf_estimated_job_cost = estimate_costs(models, sqft_value, description_value, structure_value)

            show_estimates(average_bid_price, average_job_cost, 
                           ridge_estimated_bid_price, ridge_estimated_job_cost, 
                           rf_estimated_bid_price, rf_estimated_job_cost)

            # Clear input fields
            structure_type.set('')
            lower_limit_input.delete(0, END)
            upper_limit_input.delete(0, END)      
        
        else:
            print("Sorry, we do not have any data for that type of project.")
            messagebox.showwarning("No Results", 
                    "Sorry, we do not have any data for that type of project.")

        try:
            ################### Matplotlib Charts Below ######################
            # Updated bar chart to include 'Profit and Loss %' row.
            # most_recent = projects.tail()
            most_recent = projects.tail().copy() # Use .copy() to avoid SettingWithCopyWarning

            # Plot only the numeric bar-series columns.
            chart_columns = most_recent[['SqFt', 'Bid Price', 'Job Cost']]

            chart = chart_columns.plot(kind='bar')

            # Ensure 'Bid Price' and 'Job Cost' are cast to float before formatting.
            most_recent['Bid Price'] = most_recent['Bid Price'].astype(float)
            most_recent['Job Cost'] = most_recent['Job Cost'].astype(float)

            # Format 'Bid Price' and 'Job Cost' to be rounded to the nearest two digits
            most_recent['Formatted Bid Price'] = most_recent['Bid Price'].apply(lambda x: f"{x:,.2f}")
            most_recent['Formatted Job Cost'] = most_recent['Job Cost'].apply(lambda x: f"{x:,.2f}")

            # Add the table with all columns including 'Profit and Loss %'
            table_data = most_recent[['SqFt', 'Bid Price', 'Job Cost',  
                                        'Profit and Loss %']].T
            table_data.columns = most_recent.index

            table = plt.table(cellText=table_data.values, rowLabels=table_data.index, 
                              colLabels=table_data.columns, loc='bottom', 
                              cellLoc='center', rowLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1) # Adjust the scaling to match the chart size

            chart.set_title(f"Most Recent {description_value} Projects Around {sqft_value} sqft", 
                            fontsize=16)
            chart.set_xlabel("Job Numbers", fontsize=14)
            chart.set_ylabel("Amount", fontsize=14)
            chart.legend(loc='upper right')
            chart.grid(visible=True, axis="y")

            display_text = f"The average bid price is: ${average_bid_price:,.2f} \n"
            display_text += f"The average job cost is: ${average_job_cost:,.2f}"
            plt.text(.01, .97, display_text, ha='left', va='top', 
                        transform=chart.transAxes)

            chart.axes.get_xaxis().set_visible(False)
            # Adjust the layout to fit the table and chart
            plt.subplots_adjust(left=0.2, bottom=0.2) 

            # Add tooltips to display label and value.
            cursor = mplcursors.cursor(chart, hover=True)
            cursor.connect("add", lambda sel: sel.annotation.set_text(f'{sel.artist.get_label()}: {sel.target[1]:,.2f}'))

            # Set the window title
            plt.gcf().canvas.manager.set_window_title(f"{sqft_value}_{description_value}_{todays_date}")

            plt.show()
            
            # New line chart for trend over time
            projects.loc[:, 'Awarded Date'] = pd.to_datetime(projects['Awarded Date'])
            projects = projects.sort_values('Awarded Date')

            plt.figure()
            line1, = plt.plot(projects['Awarded Date'], projects['Bid Price'], 
                                label='Bid Price', marker='o')
            line2, = plt.plot(projects['Awarded Date'], projects['Job Cost'], 
                                label='Job Cost', marker='o')
            plt.title(f"Trend of {sqft_value} sqft {description_value} Projects Over Time")
            plt.xlabel("Awarded Date")
            plt.xticks(rotation=45)
            plt.ylabel("Amount")
            plt.legend()
            plt.grid(True)

            # Add tooltips to display label and value.
            cursor = mplcursors.cursor([line1, line2], hover=True)
            cursor.connect("add", lambda sel: sel.annotation.set_text(f'{sel.artist.get_label()}: {sel.target[1]:,.2f}'))

            plt.tight_layout()
            plt.gcf().canvas.manager.set_window_title(f"Trend of {sqft_value}_{description_value}_{todays_date}")
            plt.show()

        except IndexError:
            print("Sorry, we do not have any chart information for that type of project to display.")
        except ZeroDivisionError:
            print("Sorry, we do not have any chart information for that type of project to display.")

# Fetch data from PostgreSQL
df = fetch_data_from_postgresql()

# Train models
models = train_models(df)

# Function to evaluate models
def on_closing():
    """
    Handles the closing event of the main Tkinter window.

    This function is called when the user attempts to close the main window.
    It evaluates the performance of the trained models by calling the 
    evaluate_models function and then destroys the Tkinter root window.

    Parameters:
    None

    Returns:
    None
    """
    evaluate_models(models)
    root.destroy()


def on_description_change(event):
    """
    Handles the event when the description combobox selection changes.

    This function is called when the user selects a different description 
    from the combobox. If the selected description is "Interior Demolition",
    it sets the structure type to "Other".

    Parameters:
    event (Event): The event object containing information about the 
    combobox selection change.

    Returns:
    None
    """
    if description.get() == "Interior Demolition":
        structure_type.set("Other")


# ===========================================================================
# ========================= Tkinter GUI Setup ===============================
# ===========================================================================
if __name__=="__main__":
    root = Tk()
    root.minsize(width=150, height=150)
    root.title("Demolition Estimating")
    root.config(padx=50, pady=50)

    description_label = Label(root, text="Description")
    description_label.grid(column=0, row=0, padx=5, pady=5)
    description = ttk.Combobox(root, state="readonly", 
                            values=[
                                'Interior Demolition', 
                                'Building Demo', 
                                'House Demo',
                                ]
                                )
    description.grid(column=1, row=0, padx=5, pady=5)
    description.bind("<<ComboboxSelected>>", on_description_change)

    structure_label = Label(root, text="Building Structure Type")
    structure_label.grid(column=0, row=1, padx=5, pady=5)
    create_tooltip(structure_label, "Enter structure type if it's a structure demo project."
                                    "\nEnter 'Other' if it's an Interior Demolition project.")
    structure_type = ttk.Combobox(root, state="readonly", 
                            values=[
                                'Concrete', 
                                'Wood', 
                                'Metal',
                                'Brick or Block',
                                'Other',
                                ]
                            )
    structure_type.grid(column=1, row=1, padx=5, pady=5)

    total_sqft_label = Label(root, text="Total SqFt")
    total_sqft_label.grid(column=0, row=2, padx=5, pady=2)
    sqft_input = Entry(root)
    sqft_input.grid(column=1, row=2, padx=5, pady=2)

    lower_limit_label = Label(root, text="Lower Limit")
    lower_limit_label.grid(column=0, row=3, padx=5, pady=2)
    create_tooltip(lower_limit_label, "Enter the lower square footage limit.")
    lower_limit_input = Entry(root)
    lower_limit_input.grid(column=1, row=3, padx=5, pady=2)

    upper_limit_label = Label(root, text="Upper Limit")
    upper_limit_label.grid(column=0, row=4, padx=5, pady=2)
    create_tooltip(upper_limit_label, "Enter the upper square footage limit.")
    upper_limit_input = Entry(root)
    upper_limit_input.grid(column=1, row=4, padx=4, pady=2)

    submit_button = ttk.Button(root, text="Estimate", command=estimate_button)
    submit_button.grid(column=1, row=5, padx=5, pady=10)

    # Set the protocol for window closing
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

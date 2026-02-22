import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext, font
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
from datetime import datetime
from idlelib.tooltip import Hovertip

# ============================================================================ #
# ==================================== INFO ================================== #
# ============================================================================ #
#
# ============================================================================ #
# ==================================== TODO ================================== #
# ============================================================================ #
# TODO: 
# ============================================================================ #

todays_date = datetime.now().strftime("%m%d%Y")

# ============================================================================ #
# ======================== Get Data from CSV File ============================ #
# ============================================================================ #
def fetch_data_from_csv():
    """
    Fetches project data from a CSV file and processes it.

    This function reads data from a CSV file, sets the 'Job Number' column as the
    index, and calculates the 'Profit and Loss %' for each project. 
    The processed data is then returned as a DataFrame.

    Parameters:
    None

    Returns:
    DataFrame: A pandas DataFrame containing the project data with an additional
    'Profit and Loss %' column.
    """
    data = pd.read_csv("financials/sample_data/test_company_project_data_(02122026).csv", 
                        index_col='Job Number') # Includes Structure Type and Estimator
    df = pd.DataFrame(data)

    # Data with 'Profit and Loss %'
    df['Profit and Loss %'] = round(((df['Bid Price'] - df['Job Cost'])\
         / df['Bid Price']) * 100, 2)
    # Display the dataframe with the new column
    print("\nData from CSV file")
    print("\nDataframe with 'Profit and Loss %' column:")
    print(df.tail())
    return df

# ============================================================================ #
# ======================= Estimate costs using models ======================== #
# ============================================================================ #
def train_models(df):
    """
    Trains multiple machine learning models to predict bid prices and job costs.

    This function performs the following steps:
    1. Splits the input DataFrame into training and testing sets.
    2. Defines a column transformer for one-hot encoding categorical features 
       and scaling numerical features.
    3. Creates polynomial features for the models.
    4. Trains Ridge Regression models for bid price and job cost predictions.
    5. Trains Gradient Boosting models with hyperparameter tuning for bid price
       and job cost predictions.
    6. Trains XGBoost models for bid price and job cost predictions.

    Parameters:
    df (DataFrame): The input DataFrame containing the features and target 
    variables.

    Returns:
    tuple: A tuple containing the trained models and the testing sets:
        - lr_bid_pipeline: Trained Ridge Regression model for bid price.
        - lr_cost_pipeline: Trained Ridge Regression model for job cost.
        - gb_bid_model.best_estimator_: Best estimator from the Gradient 
          Boosting model for bid price.
        - gb_cost_model.best_estimator_: Best estimator from the Gradient 
          Boosting model for job cost.
        - xgb_bid_pipeline: Trained XGBoost model for bid price.
        - xgb_cost_pipeline: Trained XGBoost model for job cost.
        - X_test: Testing set features.
        - y_bid_test: Testing set target variable for bid price.
        - y_cost_test: Testing set target variable for job cost.
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
    
    # Polynomial Features
    poly = PolynomialFeatures(degree=2, include_bias=False)

    # Ridge Regression models
    lr_bid_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                      ('poly', poly),
                                      ('model', Ridge())])
    lr_bid_pipeline.fit(X_train, y_bid_train)

    lr_cost_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                       ('poly', poly),
                                       ('model', Ridge())])
    lr_cost_pipeline.fit(X_train, y_cost_train)

    # Gradient Boosting models with hyperparameter tuning
    gb_params = {
        'model__n_estimators': [50, 100, 200],
        'model__learning_rate': [0.01, 0.1, 0.2],
        'model__max_depth': [3, 5, 7]
    }

    # n_jobs for RandomizedSearchCV is set to 1 to limit sklearn to a single 
    # thread to help prevent thread thrashing.
    gb_bid_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                      ('model', GradientBoostingRegressor(random_state=42))])
    gb_bid_model = RandomizedSearchCV(gb_bid_pipeline, gb_params, cv=5, 
                                      n_jobs=1, n_iter=10, random_state=42) #n_jobs=-1 uses all cores
    gb_bid_model.fit(X_train, y_bid_train)

    gb_cost_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                       ('model', GradientBoostingRegressor(random_state=42))])
    gb_cost_model = RandomizedSearchCV(gb_cost_pipeline, gb_params, cv=5, 
                                       n_jobs=1, n_iter=10, random_state=42) #n_jobs=-1 uses all cores
    gb_cost_model.fit(X_train, y_cost_train)

    # XGBoost models
    # n_jobs for XGBRegressor is set to None to allow XGBoost to use all available 
    # threads to help prevent thread thrashing.
    xgb_bid_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                       ('model', xgb.XGBRegressor(random_state=42, 
                                                                  n_jobs=None))])
    xgb_bid_pipeline.fit(X_train, y_bid_train)

    xgb_cost_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                       ('model', xgb.XGBRegressor(random_state=42,
                                                                  n_jobs=None))])
    xgb_cost_pipeline.fit(X_train, y_cost_train)

    return lr_bid_pipeline, lr_cost_pipeline, gb_bid_model.best_estimator_, \
        gb_cost_model.best_estimator_, xgb_bid_pipeline, xgb_cost_pipeline, \
        X_test, y_bid_test, y_cost_test

# =========================================================================== #
# ======================= Estimate costs using models ======================= #
# =========================================================================== #
def estimate_costs(models, square_feet, description, structure_type):
    """
    Estimate bid prices and job costs using multiple machine learning models.

    Parameters:
    models (list): A list containing six trained machine learning models in the 
    following order:
    [lr_bid_model, lr_cost_model, gb_bid_model, gb_cost_model, 
    xgb_bid_model, xgb_cost_model]
    square_feet (float): The square footage of the project.
    description (str): A description of the project(e.g., Building Demo, 
    House Demo, Interior Demolition).
    structure_type (str): The type of structure (e.g., Wood, Metal, Other).

    Returns:
    tuple: A tuple containing six estimated values in the following order:
           (lr_estimated_bid_price, lr_estimated_job_cost, 
            gb_estimated_bid_price, gb_estimated_job_cost, 
            xgb_estimated_bid_price, xgb_estimated_job_cost)
    """
    lr_bid_model, lr_cost_model, gb_bid_model, gb_cost_model, xgb_bid_model, \
    xgb_cost_model = models[:6]
    input_data = pd.DataFrame([[description, structure_type, square_feet]], 
                              columns=['Description', 'Structure Type', 'SqFt'])
    lr_estimated_bid_price = lr_bid_model.predict(input_data)[0]
    lr_estimated_job_cost = lr_cost_model.predict(input_data)[0]
    gb_estimated_bid_price = gb_bid_model.predict(input_data)[0]
    gb_estimated_job_cost = gb_cost_model.predict(input_data)[0]
    xgb_estimated_bid_price = xgb_bid_model.predict(input_data)[0]
    xgb_estimated_job_cost = xgb_cost_model.predict(input_data)[0]

    return lr_estimated_bid_price, lr_estimated_job_cost, \
        gb_estimated_bid_price, gb_estimated_job_cost, \
        xgb_estimated_bid_price, xgb_estimated_job_cost

# ============================================================================ #
# ======================= New Evaluate model performance ===================== #
# ============================================================================ #
def on_closing_performance_data(root):
    if root:
        root.quit()
        root.destroy()


def show_performance_data(mae_bid_lr, mse_bid_lr, r2_bid_lr, 
                          mae_cost_lr, mse_cost_lr, r2_cost_lr, 
                          mae_bid_gb, mse_bid_gb, r2_bid_gb, 
                          mae_cost_gb, mse_cost_gb, r2_cost_gb,
                          mae_bid_xgb, mse_bid_xgb, r2_bid_xgb, 
                          mae_cost_xgb, mse_cost_xgb, r2_cost_xgb):
    """
    Display the performance data of multiple machine learning models in a GUI window.

    Parameters:
    mae_bid_lr (float): Mean Absolute Error for the Linear Regression bid price model.
    mse_bid_lr (float): Mean Squared Error for the Linear Regression bid price model.
    r2_bid_lr (float): R-squared value for the Linear Regression bid price model.
    mae_cost_lr (float): Mean Absolute Error for the Linear Regression job cost model.
    mse_cost_lr (float): Mean Squared Error for the Linear Regression job cost model.
    r2_cost_lr (float): R-squared value for the Linear Regression job cost model.
    mae_bid_gb (float): Mean Absolute Error for the Gradient Boosting bid price model.
    mse_bid_gb (float): Mean Squared Error for the Gradient Boosting bid price model.
    r2_bid_gb (float): R-squared value for the Gradient Boosting bid price model.
    mae_cost_gb (float): Mean Absolute Error for the Gradient Boosting job cost model.
    mse_cost_gb (float): Mean Squared Error for the Gradient Boosting job cost model.
    r2_cost_gb (float): R-squared value for the Gradient Boosting job cost model.
    mae_bid_xgb (float): Mean Absolute Error for the XGBoost bid price model.
    mse_bid_xgb (float): Mean Squared Error for the XGBoost bid price model.
    r2_bid_xgb (float): R-squared value for the XGBoost bid price model.
    mae_cost_xgb (float): Mean Absolute Error for the XGBoost job cost model.
    mse_cost_xgb (float): Mean Squared Error for the XGBoost job cost model.
    r2_cost_xgb (float): R-squared value for the XGBoost job cost model.

    Returns:
    None
    """
    root = Tk()
    root.title("Model Performance Data")

    # Customize font and colors
    custom_font = font.Font(family="Times New Roman", size=12)

    text_area = scrolledtext.ScrolledText(root, wrap=WORD, width=40, height=20,
                                          font=custom_font, fg="green")
    text_area.pack(padx=10, pady=10)

    performance_data = (
        f"LR Bid Price: \nMAE: {mae_bid_lr:,.2f} \nMSE: {mse_bid_lr:,.2f} \nR²: {r2_bid_lr:,.2f}\n"
        f"LR Job Cost: \nMAE: {mae_cost_lr:,.2f} \nMSE: {mse_cost_lr:,.2f} \nR²: {r2_cost_lr:,.2f}\n"
        f"GB Bid Price: \nMAE: {mae_bid_gb:,.2f} \nMSE: {mse_bid_gb:,.2f} \nR²: {r2_bid_gb:,.2f}\n"
        f"GB Job Cost: \nMAE: {mae_cost_gb:,.2f} \nMSE: {mse_cost_gb:,.2f} \nR²: {r2_cost_gb:,.2f}\n"
        f"XGB Bid Price: \nMAE: {mae_bid_xgb:,.2f} \nMSE: {mse_bid_xgb:,.2f} \nR²: {r2_bid_xgb:,.2f}\n"
        f"XGB Job Cost: \nMAE: {mae_cost_xgb:,.2f} \nMSE: {mse_cost_xgb:,.2f} \nR²: {r2_cost_xgb:,.2f}\n"
    )

    text_area.insert(END, performance_data)

    # Set the protocol for window closing
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing_performance_data(root))

    root.mainloop()

# ============================================================================ #
# ======================= New Evaluate model performance ===================== #
# ============================================================================ #
def evaluate_models(models):
    """
    Evaluate the performance of multiple machine learning models on test data 
    and display the results.

    Parameters:
    models (list): A list containing the following elements in order:
        [lr_bid_model, lr_cost_model, gb_bid_model, gb_cost_model, 
        xgb_bid_model, xgb_cost_model, X_test, y_bid_test, y_cost_test]
        - lr_bid_model: Trained Linear Regression model for bid price prediction.
        - lr_cost_model: Trained Linear Regression model for job cost prediction.
        - gb_bid_model: Trained Gradient Boosting model for bid price prediction.
        - gb_cost_model: Trained Gradient Boosting model for job cost prediction.
        - xgb_bid_model: Trained XGBoost model for bid price prediction.
        - xgb_cost_model: Trained XGBoost model for job cost prediction.
        - X_test: Test features.
        - y_bid_test: True bid price values for the test set.
        - y_cost_test: True job cost values for the test set.

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
    lr_bid_model, lr_cost_model, gb_bid_model, gb_cost_model, xgb_bid_model, \
        xgb_cost_model, X_test, y_bid_test, y_cost_test = models

    # Predictions for Linear Regression
    y_bid_pred_lr = lr_bid_model.predict(X_test)
    y_cost_pred_lr = lr_cost_model.predict(X_test)

    # Predictions for Gradient Boosting
    y_bid_pred_gb = gb_bid_model.predict(X_test)
    y_cost_pred_gb = gb_cost_model.predict(X_test)

    # Predictions for XGBoost
    y_bid_pred_xgb = xgb_bid_model.predict(X_test)
    y_cost_pred_xgb = xgb_cost_model.predict(X_test)

    # Evaluation for Linear Regression
    mae_bid_lr = mean_absolute_error(y_bid_test, y_bid_pred_lr)
    mse_bid_lr = mean_squared_error(y_bid_test, y_bid_pred_lr)
    r2_bid_lr = r2_score(y_bid_test, y_bid_pred_lr)

    mae_cost_lr = mean_absolute_error(y_cost_test, y_cost_pred_lr)
    mse_cost_lr = mean_squared_error(y_cost_test, y_cost_pred_lr)
    r2_cost_lr = r2_score(y_cost_test, y_cost_pred_lr)

    # Evaluation for Gradient Boosting
    mae_bid_gb = mean_absolute_error(y_bid_test, y_bid_pred_gb)
    mse_bid_gb = mean_squared_error(y_bid_test, y_bid_pred_gb)
    r2_bid_gb = r2_score(y_bid_test, y_bid_pred_gb)

    mae_cost_gb = mean_absolute_error(y_cost_test, y_cost_pred_gb)
    mse_cost_gb = mean_squared_error(y_cost_test, y_cost_pred_gb)
    r2_cost_gb = r2_score(y_cost_test, y_cost_pred_gb)

    # Evaluation for XGBoost
    mae_bid_xgb = mean_absolute_error(y_bid_test, y_bid_pred_xgb)
    mse_bid_xgb = mean_squared_error(y_bid_test, y_bid_pred_xgb)
    r2_bid_xgb = r2_score(y_bid_test, y_bid_pred_xgb)

    mae_cost_xgb = mean_absolute_error(y_cost_test, y_cost_pred_xgb)
    mse_cost_xgb = mean_squared_error(y_cost_test, y_cost_pred_xgb)
    r2_cost_xgb = r2_score(y_cost_test, y_cost_pred_xgb)

    print("\n")
    print("----- Model Performance Data -----")
    print("Linear Regression - Bid Price:")
    print(f"MAE: {mae_bid_lr:,.2f} | MSE: {mse_bid_lr:,.2f} | R²: {r2_bid_lr:,.2f}")
    print("Linear Regression - Job Cost:")
    print(f"MAE: {mae_cost_lr:,.2f} | MSE: {mse_cost_lr:,.2f} | R²: {r2_cost_lr:,.2f}")
    print("\n")
    print("Gradient Boosting - Bid Price:")
    print(f"MAE: {mae_bid_gb:,.2f} | MSE: {mse_bid_gb:,.2f} | R²: {r2_bid_gb:,.2f}")
    print("Gradient Boosting - Job Cost:")
    print(f"MAE: {mae_cost_gb:,.2f} | MSE: {mse_cost_gb:,.2f} | R²: {r2_cost_gb:,.2f}")
    print("\n")
    print("XGBoost - Bid Price:")
    print(f"MAE: {mae_bid_xgb:,.2f} | MSE: {mse_bid_xgb:,.2f} | R²: {r2_bid_xgb:,.2f}")
    print("XGBoost - Job Cost:")
    print(f"MAE: {mae_cost_xgb:,.2f} | MSE: {mse_cost_xgb:,.2f} | R²: {r2_cost_xgb:,.2f}")

    show_performance_data(mae_bid_lr, mse_bid_lr, r2_bid_lr, 
                          mae_cost_lr, mse_cost_lr, r2_cost_lr, 
                          mae_bid_gb, mse_bid_gb, r2_bid_gb, 
                          mae_cost_gb, mse_cost_gb, r2_cost_gb,
                          mae_bid_xgb, mse_bid_xgb, r2_bid_xgb, 
                          mae_cost_xgb, mse_cost_xgb, r2_cost_xgb)

# ============================================================================ #
# ========================== Main Program ==================================== # 
# ============================================================================ #
def on_closing_estimates(info):
    if info:
        info.quit()
        info.destroy()


def create_tooltip(widget, text):
    """Creates tooltips for the tkinter launch_demo_window widgets"""
    Hovertip(widget, text, hover_delay=500)

# ============================================================================ #
# ========================== Show Estimates ================================== # 
# ============================================================================ #
def show_estimates(average_bid_price, average_job_cost, 
                       lr_estimated_bid_price, lr_estimated_job_cost, 
                       gb_estimated_bid_price, gb_estimated_job_cost,
                       xgb_estimated_bid_price, xgb_estimated_job_cost):
    """
    Displays a window with various estimate details for a demolition project.

    Parameters:
    average_bid_price (float): The average bid price for similar projects.
    average_job_cost (float): The average job cost for similar projects.
    lr_estimated_bid_price (float): The bid price estimated using a linear
        regression model.
    lr_estimated_job_cost (float): The job cost estimated using a linear
        regression model.
    gb_estimated_bid_price (float): The bid price estimated using a gradient
        boosting model.
    gb_estimated_job_cost (float): The job cost estimated using a gradient
        boosting model.
    xgb_estimated_bid_price (float): The bid price estimated using an XGBoost
        model.
    xgb_estimated_job_cost (float): The job cost estimated using an XGBoost
        model.

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
    lr_per_profit = round(int(lr_estimated_bid_price - lr_estimated_job_cost)\
         / lr_estimated_bid_price * 100, 2)
    gb_per_profit = round(int(gb_estimated_bid_price - gb_estimated_job_cost)\
         / gb_estimated_bid_price * 100, 2)
    xgb_per_profit = round(int(xgb_estimated_bid_price - xgb_estimated_job_cost)\
         / xgb_estimated_bid_price * 100, 2)

    estimates = (
        f"{description.get()} Estimates:\n\n"
            "Historical Data:\n"     
            f"Average Bid Price: ${average_bid_price:,.2f}\n"
            f"Average Job Cost: ${average_job_cost:,.2f}\n"
            f"Average % Profit: {avg_per_profit}%\n\n"
            "Machine Learning Models:\n"
            f"LR Bid Price: ${lr_estimated_bid_price:,.2f}\n"
            f"LR Job Cost: ${lr_estimated_job_cost:,.2f}\n"
            f"LR % Profit: {lr_per_profit}%\n\n"
            f"GB Bid Price: ${gb_estimated_bid_price:,.2f}\n"
            f"GB Job Cost: ${gb_estimated_job_cost:,.2f}\n"
            f"GB % Profit: {gb_per_profit}%\n\n"
            f"XGB Bid Price: ${xgb_estimated_bid_price:,.2f}\n"
            f"XGB Job Cost: ${xgb_estimated_job_cost:,.2f}\n"
            f"XGB % Profit: {xgb_per_profit:,.2f}%\n"
        )
    
    text_area.insert(END, estimates)

    # Set the protocol for window closing
    info.protocol("WM_DELETE_WINDOW", lambda: on_closing_estimates(info))

    info.mainloop()

# ============================================================================ #
# ============================== Estimate Button ============================= #
# ============================================================================ #
def estimate_button():
        """
        Handles the estimation process based on user input and selected 
        description.

        This function retrieves user input values for description, square footage,
        lower limit, and upper limit. It the filters the project data based on 
        these inputs and calculates average job cost and bid price. It directly
        displays the estimates in a new window. Additionally, it also
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
            - Estimates using historical data and machine learning models.
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

            lr_estimated_bid_price, lr_estimated_job_cost, gb_estimated_bid_price, \
                gb_estimated_job_cost, xgb_estimated_bid_price, xgb_estimated_job_cost = \
                estimate_costs(models, sqft_value, description_value, structure_value)

            show_estimates(average_bid_price, average_job_cost, 
                       lr_estimated_bid_price, lr_estimated_job_cost, 
                       gb_estimated_bid_price, gb_estimated_job_cost,
                       xgb_estimated_bid_price, xgb_estimated_job_cost)

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
            # most_recent = projects.tail()
            most_recent = projects.tail().copy() # Use .copy() to avoid SettingWithCopyWarning

            # Exclude 'Profit and Loss %' column from the bar chart.
            chart_columns = most_recent.drop(columns=['Profit and Loss %'])

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


# Fetch data from CSV file
df = fetch_data_from_csv()


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


# ============================================================================ #
# ========================= Tkinter GUI Setup ================================ #
# ============================================================================ #
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

submit_button = Button(root, text="Estimate", command=estimate_button)
submit_button.grid(column=1, row=5, padx=5, pady=5)

# Set the protocol for window closing
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

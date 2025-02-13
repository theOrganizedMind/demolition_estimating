# Demolition Estimating [estimating_main.py]

This project is a demolition estimating application that uses machine learning 
models to predict bid prices and job costs for various demolition projects. 
The application includes a Tkinter-based GUI for user interaction and 
visualization of project data.

## Features

- Fetches project data from a CSV file.
- Trains multiple machine learning models (Linear Regression, Gradient Boosting,
  XGBoost) to predict bid prices and job costs.
- Displays estimates using historical data and machine learning models.
- Generates bar charts and line charts to visualize project data.
- Provides a GUI for user interaction, including input fields for project details
 and buttons to trigger estimations and display results.

# Estimate Project [estimate_project.py]

This module is part of the Demolition Estimating application. It provides a 
Tkinter-based GUI for selecting a project description and launching the appropriate
 project window for inputting specific project details.

## Features

- A dropdown menu to select the project description (Interior Demolition, Building
  Demo, House Demo).
- Based on the selected description, it initializes the appropriate class and 
  launches the corresponding project window.
- Displays an error message if the selected description is invalid.

## Requirements

- Python 3.x
- pandas
- matplotlib
- mplcursors
- tkinter
- scikit-learn
- xgboost

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/theOrganizedMind/demolition_estimating.git
    ```

2. Navigate to the project directory:
    ```sh
    cd demolition_estimating
    ```

3. Install the required packages:
    ```
    requirements.txt
    ```

## Usage

1. Run the main application:
    ```sh
    python estimating_main.py
    ```

2. The main window will open, allowing you to input project details and 
estimate costs.

## File Structure

- [estimating_main.py]: Main application file containing the
  logic for fetching 
  data, training models, and displaying estimates.
- [estimate_project.py]: Main application file containing the logic for 
  selecting a project description and launching the appropriate project window.
- [equipment_cost.py]: Module for handling equipment cost estimation.
- [project_test_data(01122025).csv]: Sample CSV file containing project data.

## Functions

### [estimating_main.py]

- [fetch_data_from_csv()]: Fetches project data from a CSV file and processes it.
- [train_models(df)]: Trains multiple machine learning models to predict bid 
  prices and job costs.
- [estimate_costs(models, square_feet, description, structure_type)]: Estimates 
  bid prices and job costs using trained models.
- [evaluate_models(models)]: Evaluates the performance of trained models on test 
  data and displays the results.
- [show_estimates(...)]: Displays a window with various estimate details for a 
  demolition project.
- [estimate_button()]: Handles the estimation process based on user input and 
  selected description.
- [on_closing()]: Handles the closing event of the main Tkinter window.
- [on_description_change(event)] Handles the event when the description combobox 
  selection changes.

### [estimate_project.py]

- [estimate_project()]: Estimates the project based on the selected description. 
  Initializes the appropriate class and launches the corresponding project window.

### [equipment_cost.py]

- `launch_equipment_cost_window()`: Launches the Equipment Cost window application.
- `update_equipment_list(event)`: Updates the equipment list dropdown menu based 
  on the selected project type.
- `add_button()`: Adds equipment details to the project equipment dictionary.
- `finish_button()`: Displays a summary of the project equipment and their total 
  cost in a pop-up window.

## Classes

### [estimate_project.py]

- [InteriorDemo]: Class for handling interior demolition projects.
- [BuildingDemo]: Class for handling building demolition projects.
- [HouseDemo]: Class for handling house demolition projects.

## TODO

## License

This project is licensed under the MIT License. See the LICENSE file for details.
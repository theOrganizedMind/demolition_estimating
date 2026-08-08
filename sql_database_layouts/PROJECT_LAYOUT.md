# Demolition Estimating SQL Database Layout: 

This document describes the columns, types, and possible values for a demolition
company SQL database.

---

## Project SQL Database Layout

| Column Name      | Type                | Example Values / Notes                                                                 |
|------------------|---------------------|----------------------------------------------------------------------------------------|
| **project_id**   | int PRIMARY KEY     | 1                                           
| **job_number**   | VARCHAR(20)         | 0064875                                        
| **awarded_date** | DATE                | 2024-06-24                                                           
| **project_description**| VARCHAR(50)   | Example (Interior Demolition)                               
| **structure_type**| VARCHAR(50)        | Example (Wood, Metal)
| **sqft**         | INTEGER             | Example (12000)
| **bid_price**    | FLOAT               | Example (25000)
| **job_cost**     | FLOAT               | Example (12500)
| **estimator**    | VARCHAR(255)        | Estimator Name


---

## Notes

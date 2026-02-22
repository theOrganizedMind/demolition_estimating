
loans = {
    "Loan #1": 8800.89,
    "Loan #2": 3434.43,
}

subscriptions = {
    "Phone": 435.94,
    "IT Support": 130.00,
    "Accounting": 260.00,
    "Website": 18.65,
    "Other": 23.60,
    "Bidding Software": 190.00,
}

insurance = {
    "Auto": 9140.75,
    "Health": 1200.00,
}

monthly_expenses = {
    "Loans": sum(loans.values()),
    "Insurance": sum(insurance.values()),
    "Subscriptions": sum(subscriptions.values()),
    "Building Rent": 11077.53,
    }

quickbooks_monthly_expenses = {
    "2023-01": 24_500.00, "2023-02": 38_200.00, "2023-03": 35_750.00,
    "2023-04": 42_100.00, "2023-05": 31_900.00, "2023-06": 120_000.00,
    "2023-07": 80_000.00, "2023-08": 145_000.00, "2023-09": 140_000.00,
    "2023-10": 110_000.00, "2023-11": 90_000.00, "2023-12": 78_000.00,
    "2024-01": 100_000.00,
}

if __name__ == "__main__":
    monthly_expenses = round(sum(monthly_expenses.values()), 2)
    print(f"The total monthly expenses = ${monthly_expenses:,.2f}")
    total_loans = round(sum(loans.values()), 2)
    print(f"The total monthly loans = ${total_loans:,.2f}")

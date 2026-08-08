
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

if __name__ == "__main__":
    monthly_expenses = round(sum(monthly_expenses.values()), 2)
    print(f"The total monthly expenses = ${monthly_expenses:,.2f}")
    total_loans = round(sum(loans.values()), 2)
    print(f"The total monthly loans = ${total_loans:,.2f}")

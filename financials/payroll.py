employees = {
    "John Doe": 50000,
    "Jane Smith": 60000,
    "Alice Johnson": 55000,
    "Bob Brown": 58000,
    "Carol White": 62000,
    "David Black": 61000,
}

monthly_payroll = {
    "2023-01": 8746.96, "2023-02": 5139.33, "2023-03": 9609.84, "2023-04": 7841.84, 
    "2023-05": 2373.33, "2023-06": 9105.77, "2023-07": 7241.33, "2023-08": 6054.70, 
    "2023-09": 18583.62, "2023-10": 9554.24, "2023-11": 6924.12, "2023-12": 6883.61,
    "2024-01": 11019.29,
}

if __name__ == "__main__":
    total_yearly_payroll = (sum(employees.values()))
    print(f"Total yearly payroll = ${total_yearly_payroll:,.2f}")
    total_monthly_payroll = (sum(employees.values()) / 12)
    print(f"Total monthly payroll = ${total_monthly_payroll:,.2f}")
    total_weekly_payroll = (sum(employees.values()) / 52)
    print(f"Total weekly payroll = ${total_weekly_payroll:,.2f}")
    total_num_employees = len(employees)
    print(f"Total number of employees: {total_num_employees}")

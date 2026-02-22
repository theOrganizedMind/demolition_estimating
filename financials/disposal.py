monthly_disposal_cost = {
    "2023-01": 28746.96, "2023-02": 75139.33, "2023-03": 9609.84, "2023-04": 7841.84, 
    "2023-05": 22373.33, "2023-06": 89105.77, "2023-07": 47241.33, "2023-08": 96054.70, 
    "2023-09": 118583.62, "2023-10": 59554.24, "2023-11": 56924.12, "2023-12": 76883.61,
    "2024-01": 111019.29,
}

if __name__ == "__main__":
    total_disposal = (sum(monthly_disposal_cost.values()))
    print(f"Total disposal cost = ${total_disposal:,.2f}")
    num_months = len(monthly_disposal_cost)
    print(f"Number of months: {num_months}")
    avg_disposal_cost = round(total_disposal / num_months, 2)
    print(f"Average monthly disposal cost = ${avg_disposal_cost:,.2f}")

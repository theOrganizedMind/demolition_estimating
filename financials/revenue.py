revenue = {
    "2023": {
        "revenue": 338_067.88,
        "net profit": 109_085.51,
    },
    "2024": {
        "revenue": 878_601.00,
        "net profit": 143_706.08,
    },
    "2025": {
        "revenue": 1_259_972.00,
        "net profit": 183_615.68,
    }
}

if __name__ == "__main__":
    for key, values in revenue.items():
        print(f"{key.center(20, '-')}")
        print(f"Revenue: {values['revenue']:,.2f}")
        print(f"Net profit: {values['net profit']:,.2f}")
        print(f"Profit margin: {values['net profit'] / values['revenue']:,.2%}")

from database.operations import create_account
from database.operations import create_customer

customer = create_customer(
    first_name="Bin",
    last_name="Yang",
)
print("Created customer:")
print(customer)
account = create_account(
    customer_id=customer[0],
    account_type="checking",
    starting_balance=500.00,
)
print("\nCreated account:")
print(account)
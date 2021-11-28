from ...data.reading.exchange_private_data.account_balance import available_account_balance


# todo can this be moved into octobot core?
async def cut_position_size(context, order_size, side):
    available_acc_bal = await available_account_balance(context, side)
    if available_acc_bal > order_size:
        return order_size
    else:
        return available_acc_bal

import enum

class Side(enum.Enum):
    """
    Represents the direction/nature of a portfolio transaction.
    Controls how cash balance, asset balance, and ROI are calculated.
    """

    BUY = "BUY"
    """
    User acquires an asset using portfolio cash.
    - Cash Balance: Decreases (Outflow)
    - Asset Balance: Increases (Inflow)
    - ROI Impact: Increases cost basis; no immediate profit change.
    """

    SELL = "SELL"
    """
    User liquidates an asset to receive cash.
    - Cash Balance: Increases (Inflow)
    - Asset Balance: Decreases (Outflow)
    - ROI Impact: Realizes capital gains or losses.
    """

    DEPOSIT = "DEPOSIT"
    """
    User injects external capital (cash) into the portfolio.
    - Cash Balance: Increases (Inflow from outside)
    - Asset Balance: No change
    - ROI Impact: Boosts total account value but DOES NOT count as investment profit.
    """

    WITHDRAW = "WITHDRAW"
    """
    User removes capital (cash) out of the portfolio to the outside world.
    - Cash Balance: Decreases (Outflow to outside)
    - Asset Balance: No change
    - ROI Impact: Lowers account value but DOES NOT count as an investment loss.
    """

    INCOME = "INCOME"
    """
    Portfolio assets generate free cash (Dividends, Interest, Staking rewards).
    - Cash Balance: Increases (Inflow from asset)
    - Asset Balance: No change
    - ROI Impact: Counts as pure profit; directly increases total ROI.
    """

    FEE = "FEE"
    """
    Cash or asset value lost to transaction costs, management fees, or taxes.
    - Cash/Asset Balance: Decreases (Outflow)
    - Asset Balance: May decrease if paid in asset fractions (e.g., gas fees)
    - ROI Impact: Counts as an expense; directly decreases total ROI.
    """
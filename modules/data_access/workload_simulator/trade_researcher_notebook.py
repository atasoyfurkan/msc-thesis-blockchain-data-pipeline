from modules.data_access.api_client.client import DataPipelineClient
import pandas as pd
import matplotlib.pyplot as plt
import logging

def run_trade_researcher_notebook(client: DataPipelineClient, start_index: int, end_index: int):
    """
    This function runs the trade researcher notebook for a given date range.
    It does price impact analysis.
    """
    
    # ## Pre-analysis

    # In[75]:


    transfer_bucket = "transfer-event-data"
    transfer_days = client.list_dates(bucket_name=transfer_bucket)[start_index:end_index]
    # transfer_days = days
    transfer_table_path = client.get_table_path(bucket_name=transfer_bucket, dates=transfer_days)


    # In[78]:


    result = client.execute_query(f"""
    SELECT *    
    FROM {transfer_table_path}
    LIMIT 3
    """)
    logging.debug(result)
    result


    # In[77]:


    transfer_df = client.execute_query(f"""
    SELECT symbol, value, block_created_at
    FROM {transfer_table_path}
    """)
    logging.debug(transfer_df)
    transfer_df


    # In[25]:


    plt.figure(figsize=(10, 6))
    plt.hist(transfer_df['value'], bins=50, edgecolor='black', log=True)
    plt.xlabel('Transaction Value')
    plt.ylabel('Frequency (Log Scale)')
    plt.title('Distribution of Transaction Values')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # In[40]:


    threshold_value = 1*10**7


    # In[41]:


    price_bucket = "price-data"
    price_days = client.list_dates(bucket_name=price_bucket)[start_index:end_index]
    # price_days = days
    price_table_path = client.get_table_path(bucket_name=price_bucket, dates=price_days)


    # In[42]:


    result = client.execute_query(f"""
    SELECT *    
    FROM {price_table_path}
    WHERE symbol = 'ETHUSDT'
    LIMIT 3
    """)
    logging.debug(result)
    result


    # In[43]:


    price_data_eth_df = client.execute_query(f"""
    SELECT *    
    FROM {price_table_path}
    WHERE symbol = 'ETHUSDT'
    """)
    price_data_bnb_df = client.execute_query(f"""
    SELECT *    
    FROM {price_table_path}
    WHERE symbol = 'BNBUSDT'
    """)
    logging.debug(price_data_bnb_df)


    # In[44]:


    price_data_eth_df['fetched_at'] = pd.to_datetime(price_data_eth_df['fetched_at'], format="ISO8601")
    price_data_bnb_df['fetched_at'] = pd.to_datetime(price_data_bnb_df['fetched_at'], format="ISO8601")


    # In[45]:


    plt.figure(figsize=(12, 6))
    plt.plot(price_data_eth_df['fetched_at'], price_data_eth_df['price'], label='Price', color='blue')

    # Add labels, title, and legend
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('Price Changes Over Time (ETHUSDT)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # In[46]:


    plt.figure(figsize=(12, 6))
    plt.plot(price_data_bnb_df['fetched_at'], price_data_bnb_df['price'], label='Price', color='blue')

    # Add labels, title, and legend
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('Price Changes Over Time (BNBUSDT)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # ## Analysis

    # In[47]:


    high_transfer_df = client.execute_query(f"""
    SELECT symbol, value, block_created_at
    FROM {transfer_table_path}
    WHERE value > {threshold_value}
    """)
    len(high_transfer_df)
    logging.debug(high_transfer_df)
    high_transfer_df['block_created_at'] = pd.to_datetime(high_transfer_df['block_created_at'], format="ISO8601")


    # In[48]:


    # Plot the price data
    plt.figure(figsize=(14, 7))
    plt.plot(price_data_eth_df['fetched_at'], price_data_eth_df['price'], label='Price', color='blue', linewidth=1)

    def get_closest_price(txn_time, price_data_eth_df):
        closest_price_row = price_data_eth_df.iloc[(price_data_eth_df['fetched_at'] - txn_time).abs().argsort()[:1]]
        return closest_price_row['price'].values[0] if not closest_price_row.empty else None

    high_transfer_df['price'] = high_transfer_df['block_created_at'].apply(lambda x: get_closest_price(x, price_data_eth_df))


    # Overlay high-value transactions
    plt.scatter(
        high_transfer_df['block_created_at'],  # Transaction timestamps
        high_transfer_df['price'],     # Corresponding prices
        s=high_transfer_df['value'] / 1e4*0.2,  # Scale dot size by transaction value (adjust scaling factor)
        color='red', alpha=0.7, label='High-Value Transfer'
    )

    # Add labels, legend, and grid
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('High-Value Transfers Overlaid on Price Data (ETHUSDT)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show the plot
    plt.show()


    # In[49]:


    # Plot the price data
    plt.figure(figsize=(14, 7))
    plt.plot(price_data_bnb_df['fetched_at'], price_data_bnb_df['price'], label='Price', color='blue', linewidth=1)

    def get_closest_price(txn_time, price_data_bnb_df):
        closest_price_row = price_data_bnb_df.iloc[(price_data_bnb_df['fetched_at'] - txn_time).abs().argsort()[:1]]
        return closest_price_row['price'].values[0] if not closest_price_row.empty else None

    high_transfer_df['price'] = high_transfer_df['block_created_at'].apply(lambda x: get_closest_price(x, price_data_bnb_df))


    # Overlay high-value transactions
    plt.scatter(
        high_transfer_df['block_created_at'],  # Transaction timestamps
        high_transfer_df['price'],     # Corresponding prices
        s=high_transfer_df['value'] / 1e4*0.2,  # Scale dot size by transaction value (adjust scaling factor)
        color='red', alpha=0.7, label='High-Value Transfer'
    )

    # Add labels, legend, and grid
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('High-Value Transfers Overlaid on Price Data (BNBUSDT)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show the plot
    plt.show()


    # In[35]:


    high_transfer_with_pricing_df = client.execute_query(f"""
    WITH high_value_transfers AS (
        SELECT *
        FROM {transfer_table_path}
        WHERE value > {threshold_value}
        AND symbol = 'USDT'
    ),
    before_price_data AS (
        SELECT t.transaction_hash,
            p.price AS before_price,
            p.fetched_at AS before_price_timestamp,
            DATEDIFF('second', CAST(p.fetched_at AS TIMESTAMP), CAST(t.block_created_at AS TIMESTAMP)) AS time_diff
        FROM high_value_transfers t
        LEFT JOIN {price_table_path} p
        ON p.symbol IN ('ETHUSDT')
        AND p.fetched_at < t.block_created_at -- Use block_created_at for comparison
        AND DATEDIFF('second', CAST(p.fetched_at AS TIMESTAMP), CAST(t.block_created_at AS TIMESTAMP)) >= 60
        ORDER BY t.transaction_hash, time_diff ASC -- Select the closest valid entry
    ),
    filtered_before_price AS (
        SELECT DISTINCT ON (transaction_hash) transaction_hash, before_price, before_price_timestamp
        FROM before_price_data
    ),
    after_price_data AS (
        SELECT t.transaction_hash,
            p.price AS after_price,
            p.fetched_at AS after_price_timestamp,
            DATEDIFF('second', CAST(t.block_created_at AS TIMESTAMP), CAST(p.fetched_at AS TIMESTAMP)) AS time_diff
        FROM high_value_transfers t
        LEFT JOIN {price_table_path} p
        ON p.symbol IN ('ETHUSDT')
        AND p.fetched_at > t.block_created_at -- Use block_created_at for comparison
        AND DATEDIFF('second', CAST(t.block_created_at AS TIMESTAMP), CAST(p.fetched_at AS TIMESTAMP)) >= 60
        ORDER BY t.transaction_hash, time_diff ASC -- Select the closest valid entry
    ),
    filtered_after_price AS (
        SELECT DISTINCT ON (transaction_hash) transaction_hash, after_price, after_price_timestamp
        FROM after_price_data
    ),
    combined_data AS (
        SELECT t.*,
            b.before_price,
            b.before_price_timestamp,
            a.after_price,
            a.after_price_timestamp
        FROM high_value_transfers t
        LEFT JOIN filtered_before_price b ON t.transaction_hash = b.transaction_hash
        LEFT JOIN filtered_after_price a ON t.transaction_hash = a.transaction_hash
    )
    SELECT *
    FROM combined_data
    ORDER BY CAST(block_created_at AS TIMESTAMP)
    """)


    # In[39]:


    logging.debug(high_transfer_with_pricing_df)
    high_transfer_with_pricing_df


    # In[38]:


    # Calculate price impact
    high_transfer_with_pricing_df['price_impact'] = ((high_transfer_with_pricing_df['after_price'] - high_transfer_with_pricing_df['before_price']) / high_transfer_with_pricing_df['before_price']) * 100

    # Handle missing or invalid data
    high_transfer_with_pricing_df['price_impact'] = high_transfer_with_pricing_df['price_impact'].fillna(0)  # Replace NaN values with 0 (or use another approach)
    high_transfer_with_pricing_df = high_transfer_with_pricing_df.dropna(subset=['before_price', 'after_price'])  # Remove rows with missing prices if necessary
    high_transfer_with_pricing_df[['value', 'before_price', 'after_price', 'price_impact']]


    # In[ ]:


    plt.figure(figsize=(10, 6))

    # Plot a histogram
    plt.hist(high_transfer_with_pricing_df['price_impact'], bins=30, edgecolor='black', alpha=0.7)

    # Add labels and title
    plt.xlabel('Price Impact (%)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Price Impact')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show the plot
    plt.show()


    # In[ ]:

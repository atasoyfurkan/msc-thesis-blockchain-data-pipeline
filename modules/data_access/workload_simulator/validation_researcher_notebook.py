from modules.data_access.api_client.client import DataPipelineClient
import pandas as pd
import matplotlib.pyplot as plt
import logging

def run_validation_researcher_notebook(client: DataPipelineClient, start_index: int, end_index: int):
    """
    This function runs the validation researcher notebook for a given date range.
    It does gas price and prioritiy trends analysis.
    """
    # In[41]:


    transaction_bucket = "mempool-data"
    transaction_days = client.list_dates(bucket_name=transaction_bucket)[start_index:end_index]
    transaction_table_path = client.get_table_path(bucket_name=transaction_bucket, dates=transaction_days)
    block_bucket = "block-data"
    block_days = client.list_dates(bucket_name=block_bucket)[start_index:end_index]
    block_table_path = client.get_table_path(bucket_name=block_bucket, dates=block_days)
    block_header_bucket = "block-header-data"
    block_header_days = client.list_dates(bucket_name=block_header_bucket)[start_index:end_index]
    block_header_table_path = client.get_table_path(bucket_name=block_header_bucket, dates=block_header_days)


    # In[42]:


    df = client.query(f"""
    SELECT *    
    FROM {transaction_table_path}
    LIMIT 3
    """)
    logging.debug(df)
    df


    # In[43]:


    transaction_df = client.query(f"""
    SELECT t.hash, t.estimated_effective_gas_price as gas_price, t.max_priority_fee_per_gas, t.max_fee_per_gas, t.fetched_at, t.from, t.to
    FROM {transaction_table_path} t
    """)
    logging.debug(transaction_df)


    # In[45]:


    plt.figure(figsize=(10, 6))
    plt.hist(transaction_df['gas_price'], bins=50, edgecolor='black', log=True)
    plt.xlabel('Gas Price (Gwei)')
    plt.ylabel('Frequency (Log Scale)')
    plt.title('Distribution of Gas Prices')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # In[46]:


    transaction_df['fetched_at'] = pd.to_datetime(transaction_df['fetched_at'], format="ISO8601")


    # In[47]:


    plt.figure(figsize=(12, 6))
    plt.plot(transaction_df['fetched_at'], transaction_df['gas_price'], label='Gas Price', color='blue')
    plt.xlabel('Timestamp')
    plt.ylabel('Gas Price (Gwei)')
    plt.title('Gas Price Trends Over Time')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.show()


    # In[48]:


    high_gas_price_threshold = transaction_df['gas_price'].quantile(0.97)


    # In[51]:


    high_gas_transactions_df = client.query(f"""
    SELECT hash, estimated_effective_gas_price as gas_price, max_priority_fee_per_gas, max_fee_per_gas, 
        fetched_at
    FROM {transaction_table_path}
    WHERE estimated_effective_gas_price > {high_gas_price_threshold}
    """)
    logging.debug(len(high_gas_transactions_df))
    logging.debug(high_gas_transactions_df)


    # In[52]:


    high_gas_transactions_df['fetched_at'] = pd.to_datetime(high_gas_transactions_df['fetched_at'])
    high_gas_transactions_df['time_diff'] = high_gas_transactions_df['fetched_at'].diff().dt.total_seconds()


    # In[53]:


    front_running_df = high_gas_transactions_df[(high_gas_transactions_df['time_diff'] > 0) & (high_gas_transactions_df['time_diff'] < 10)]


    # In[54]:


    front_running_df


    # In[55]:


    plt.figure(figsize=(10, 6))
    plt.hist(transaction_df['max_priority_fee_per_gas'], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('Max Priority Fee (Gwei)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Max Priority Fees')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # In[56]:


    df = client.query(f"""
    SELECT *    
    FROM {block_header_table_path}
    """)
    logging.debug(df)
    df


    # In[24]:


    sandwich_attacks_df = client.query(f"""
    WITH mempool_txns AS (
        SELECT hash, estimated_effective_gas_price AS gas_price, latest_block_base_fee_per_gas
        FROM {transaction_table_path}
    ),
    block AS (
        SELECT 
            *
        FROM {block_table_path} AS b
    ),
    enriched_txns AS (
        SELECT m.hash, 
            m.gas_price, 
            b.hash,
            b.number
        FROM mempool_txns m
        LEFT JOIN block b 
        ON m.latest_block_base_fee_per_gas = b.base_fee_per_gas
    )
    SELECT * 
    FROM enriched_txns
    """)


    # In[57]:


    logging.debug(sandwich_attacks_df)
    sandwich_attacks_df



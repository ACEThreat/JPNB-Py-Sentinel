# Install required packages
!pip install azure-kusto-data azure-kusto-ingest pandas

# Import necessary libraries
import pandas as pd
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table

# Kusto connection settings
cluster = "https://<your-cluster>.kusto.windows.net"
database = "<your-database>"
client_id = "<your-client-id>"
client_secret = "<your-client-secret>"
authority_id = "<your-tenant-id>"

# Create Kusto connection string
kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
    cluster, client_id, client_secret, authority_id
)

# Create Kusto client
client = KustoClient(kcsb)

# Define KQL query to retrieve process tree data
query = """
SecurityEvent
| where EventID == 4688
| extend ProcessName = tostring(split(CommandLine, " ")[0])
| project EventTime = TimeGenerated, Computer, Account, ProcessID, ParentProcessID, ProcessName, CommandLine
| sort by EventTime desc
"""

# Execute query
response = client.execute(database, query)
df = dataframe_from_result_table(response.primary_results[0])

# Display the first few rows of the DataFrame
df.head()

----------------

# Function to build a process tree
def build_process_tree(df):
    tree = {}
    for _, row in df.iterrows():
        pid = row['ProcessID']
        ppid = row['ParentProcessID']
        tree[pid] = tree.get(pid, {'children': [], 'details': row})
        tree[ppid] = tree.get(ppid, {'children': []})
        tree[ppid]['children'].append(tree[pid])
    return tree

# Build the process tree
process_tree = build_process_tree(df)

# Recursive function to print the process tree
def print_process_tree(tree, pid, level=0):
    if pid not in tree:
        return
    print('    ' * level + f"{tree[pid]['details']['ProcessName']} (PID: {pid})")
    for child in tree[pid]['children']:
        child_pid = child['details']['ProcessID']
        print_process_tree(tree, child_pid, level + 1)

# Print the process tree starting from the root processes
for pid in process_tree:
    if process_tree[pid]['details']['ParentProcessID'] == 0:
        print_process_tree(process_tree, pid)

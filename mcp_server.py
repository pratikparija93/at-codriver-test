from fastmcp import FastMCP
from google.cloud import bigquery
import json

# Initialize the MCP Server
mcp = FastMCP("AutoTrader Database Server")
bq_client = bigquery.Client(project="autotrader-demo-493616")

@mcp.tool()
def get_vehicle_specs(vrm: str) -> str:
    """Searches the AutoTrader database for a car's specifications based on its license plate (VRM)."""
    query = f"SELECT make, model, hard_specs, trending_buyer_intent FROM `autotrader_poc.vehicle_intelligence` WHERE vrm = '{vrm}'"
    results = bq_client.query(query).result()
    for row in results:
        return json.dumps({"make": row.make, "model": row.model, "hard_specs": row.hard_specs, "trending_intent": row.trending_buyer_intent})
    return "VRM_NOT_FOUND"

@mcp.tool()
def save_vehicle_specs(vrm: str, make: str, model: str, hard_specs: str, trending_intent: str) -> str:
    """Saves new vehicle specifications to the AutoTrader database if they do not exist."""
    query = f"""
        INSERT INTO `autotrader_poc.vehicle_intelligence` 
        (vrm, make, model, hard_specs, trending_buyer_intent)
        VALUES ('{vrm}', '{make}', '{model}', '{hard_specs}', '{trending_intent}')
    """
    bq_client.query(query).result()
    return "SUCCESS"

if __name__ == "__main__":
    mcp.run()
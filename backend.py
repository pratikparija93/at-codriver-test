import vertexai
from vertexai.generative_models import GenerativeModel, Part, Tool, FunctionDeclaration
from google.cloud import bigquery

# Initialize GCP
project_id = "autotrader-demo-493616"
vertexai.init(project=project_id, location="us-central1")
bq_client = bigquery.Client(project=project_id)

# --- Tool Execution Functions ---
def execute_get_specs(vrm):
    query = f"SELECT make, model, hard_specs, trending_buyer_intent FROM `autotrader_poc.vehicle_intelligence` WHERE vrm = '{vrm}'"
    results = bq_client.query(query).result()
    for row in results:
        return {"make": row.make, "model": row.model, "hard_specs": row.hard_specs, "trending_intent": row.trending_buyer_intent}
    return {"result": "VRM_NOT_FOUND"}

def execute_save_specs(args):
    query = f"""
        INSERT INTO `autotrader_poc.vehicle_intelligence` 
        (vrm, make, model, hard_specs, trending_buyer_intent)
        VALUES ('{args['vrm']}', '{args['make']}', '{args['model']}', '{args['hard_specs']}', '{args['trending_intent']}')
    """
    bq_client.query(query).result()
    return {"result": "SUCCESS"}

# --- The Main Agent Workflow ---
def run_agentic_workflow(image_bytes):
    thinking_steps = [] # <--- NEW: Initialize our log
    
    # 1. Vision Model extracts VRM
    thinking_steps.append("👁️ **Vision Model:** Inspecting image to extract UK License Plate...")
    vision_model = GenerativeModel("gemini-2.5-flash")
    image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
    vrm_response = vision_model.generate_content(
        [image_part, "Extract ONLY the UK license plate (VRM) from this image. Return no other text."],
        generation_config={"temperature": 0.0}
    )
    vrm = vrm_response.text.strip()
    thinking_steps.append(f"✅ **Vision Model:** Successfully extracted VRM: `{vrm}`")
    
    # 2. Define the MCP Tools for the Agent
    get_specs_func = FunctionDeclaration(
        name="get_vehicle_specs",
        description="Searches the database for car specs by VRM. Returns specs or 'VRM_NOT_FOUND'.",
        parameters={"type": "object", "properties": {"vrm": {"type": "string"}}}
    )
    save_specs_func = FunctionDeclaration(
        name="save_vehicle_specs",
        description="Saves new car specs to the database.",
        parameters={
            "type": "object", 
            "properties": {
                "vrm": {"type": "string"}, "make": {"type": "string"}, 
                "model": {"type": "string"}, "hard_specs": {"type": "string"}, 
                "trending_intent": {"type": "string"}
            }
        }
    )
    mcp_tools = Tool(function_declarations=[get_specs_func, save_specs_func])
    
    # 3. Start the Agentic Chat Loop
    thinking_steps.append("🤖 **Agent:** Waking up and assessing overarching goal...")
    agent_model = GenerativeModel("gemini-2.5-pro", tools=[mcp_tools])
    chat = agent_model.start_chat() 
    
    prompt = f"""
    You are an autonomous automotive AI. The user uploaded a car with VRM '{vrm}'. 
    Goal: Write an engaging, 3-sentence advert for this car.
    
    Rules:
    1. Use your 'get_vehicle_specs' tool to look up the car.
    2. If it returns 'VRM_NOT_FOUND', deduce the make, model, and specs from the image and use 'save_vehicle_specs' to save them.
    3. ONLY mention features that exist in the database specs.
    """
    
    response = chat.send_message([image_part, prompt])
    
    # 4. Handle the AI's requests to use tools
    while response.candidates[0].function_calls:
        function_call = response.candidates[0].function_calls[0]
        
        thinking_steps.append(f"🛠️ **Agent Decision:** Pausing generation to use tool -> `{function_call.name}`")
        
        # Execute the correct tool
        if function_call.name == "get_vehicle_specs":
            result = execute_get_specs(function_call.args["vrm"])
        elif function_call.name == "save_vehicle_specs":
            result = execute_save_specs(function_call.args)
            
        thinking_steps.append(f"📥 **Database Response:** Returning data to agent: `{result}`")
            
        # Send the tool result back to the AI
        response = chat.send_message(
            Part.from_function_response(
                name=function_call.name,
                response=result
            )
        )
        
    thinking_steps.append("✍️ **Agent:** Tool execution complete. Drafting final grounded advert...")
        
    # Return BOTH the list of steps and the final advert
    return thinking_steps, response.text
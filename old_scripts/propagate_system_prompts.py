import json
import os

def update_system_prompts():
    """Update the system message in jsonSchema.json with the content from systemPrompt.md for all agents."""
    agents_dir = 'agents'
    
    # Get all immediate subdirectories in the agents directory
    agent_folders = [f for f in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, f))]
    
    for agent_folder in agent_folders:
        try:
            # Construct paths
            system_prompt_path = os.path.join(agents_dir, agent_folder, 'systemPrompt.md')
            schema_path = os.path.join(agents_dir, agent_folder, 'jsonSchema.json')
            
            # Skip if either file doesn't exist
            if not os.path.exists(system_prompt_path) or not os.path.exists(schema_path):
                print(f"Skipping {agent_folder}: Missing required files")
                continue
            
            # Read system prompt
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read().strip()
            
            # Read and update schema
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Ensure messages array exists
            if 'messages' not in schema:
                schema['messages'] = []
            
            # Find or create system message
            system_message = next(
                (msg for msg in schema['messages'] if msg.get('role') == 'system'),
                None
            )
            
            if system_message:
                # Update existing system message
                system_message['content'] = system_prompt
            else:
                # Add new system message
                schema['messages'].append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            # Write back to file
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)
                
            print(f"Successfully updated system message in {agent_folder}/jsonSchema.json")
            
        except Exception as e:
            print(f"Error processing {agent_folder}: {str(e)}")

if __name__ == "__main__":
    update_system_prompts() 
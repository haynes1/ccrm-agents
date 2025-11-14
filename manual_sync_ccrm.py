#!/usr/bin/env python3
"""
Manual sync script for CCRM production - inserts agents directly into metadata.agent table
"""
import json
import os
import psycopg2

# Database connection
DB_URL = "postgresql://postgres:postgres@localhost:5438/default?sslmode=disable"

# Agents directory
AGENTS_DIR = "/Users/giza/code/ccrm-agents/definitions/System/Agents"

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    agents = []

    # Read all agents
    for agent_name in os.listdir(AGENTS_DIR):
        agent_path = os.path.join(AGENTS_DIR, agent_name)
        if not os.path.isdir(agent_path):
            continue

        json_path = os.path.join(agent_path, "jsonSchema.json")
        prompt_path = os.path.join(agent_path, "systemPrompt.md")

        if not os.path.exists(json_path) or not os.path.exists(prompt_path):
            continue

        with open(json_path, 'r') as f:
            schema = json.load(f)

        with open(prompt_path, 'r') as f:
            system_prompt = f.read().strip()

        agent_id = schema.get('agentId')
        description = schema.get('description', '')

        agents.append((
            agent_id,
            agent_name,
            description,
            system_prompt,
            'claude-sonnet-4-20250514',  # Default model
            agent_name == 'cc'  # Make cc the default
        ))

    # Insert agents
    for agent in agents:
        try:
            cursor.execute("""
                INSERT INTO metadata.agent
                (id, name, description, "systemPrompt", "llmModelId", "isDefault", "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    "systemPrompt" = EXCLUDED."systemPrompt",
                    "llmModelId" = EXCLUDED."llmModelId",
                    "isDefault" = EXCLUDED."isDefault",
                    "updatedAt" = NOW()
            """, agent)
            print(f"✅ Synced agent: {agent[1]}")
        except Exception as e:
            print(f"❌ Failed to sync agent {agent[1]}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎉 Successfully synced {len(agents)} agents!")

if __name__ == "__main__":
    main()

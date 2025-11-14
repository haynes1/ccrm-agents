import { MigrationInterface, QueryRunner } from 'typeorm';

export class CreateAgentSystemTables1743605310127 implements MigrationInterface {
  name = 'CreateAgentSystemTables1743605310127';

  public async up(queryRunner: QueryRunner): Promise<void> {

    // Create metadata schema if it doesn't exist
    await queryRunner.query(`CREATE SCHEMA IF NOT EXISTS "metadata"`);

    // Create Agents table
    await queryRunner.query(
      `CREATE TABLE "metadata"."agent" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "userId" uuid REFERENCES "core"."user"("id") ON DELETE SET NULL,
        "name" character varying(255) NOT NULL,
        "description" text,
        "systemPrompt" text NOT NULL,
        "llmModelId" character varying(255) NOT NULL,
        "isDefault" boolean NOT NULL DEFAULT false,
        "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        CONSTRAINT "PK_agent" PRIMARY KEY ("id")
      )`,
    );

    // Create Tools table
    await queryRunner.query(
      `CREATE TABLE "metadata"."tool" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "toolName" character varying(255) NOT NULL,
        "descriptionForLlm" text NOT NULL,
        "jsonSchema" JSONB,
        "toolType" character varying(50) NOT NULL,
        "internalApiPath" character varying(255),
        "isSystemTool" boolean NOT NULL DEFAULT true,
        "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        CONSTRAINT "UQ_tool_name" UNIQUE ("toolName"),
        CONSTRAINT "PK_tool" PRIMARY KEY ("id")
      )`,
    );

    // Create Agent_Tools junction table
    await queryRunner.query(
      `CREATE TABLE "metadata"."agent_tool" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "agentId" uuid NOT NULL REFERENCES "metadata"."agent"("id") ON DELETE CASCADE,
        "toolId" uuid NOT NULL REFERENCES "metadata"."tool"("id") ON DELETE CASCADE,
        "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        CONSTRAINT "UQ_agent_tool" UNIQUE ("agentId", "toolId"),
        CONSTRAINT "PK_agent_tool" PRIMARY KEY ("id")
      )`,
    );

    // Create User_Custom_Tool_Configurations table
    await queryRunner.query(
      `CREATE TABLE "metadata"."user_custom_tool_configuration" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "userId" uuid NOT NULL REFERENCES "core"."user"("id") ON DELETE CASCADE,
        "toolId" uuid NOT NULL REFERENCES "metadata"."tool"("id") ON DELETE CASCADE,
        "displayNameForAgent" character varying(255) NOT NULL,
        "apiEndpointUrl" character varying(2048) NOT NULL,
        "authenticationDetailsLocation" character varying(255) NOT NULL,
        "requestSchemaOverrideLocation" character varying(255),
        "descriptionOverrideLocation" character varying(255),
        "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        CONSTRAINT "PK_user_custom_tool_configuration" PRIMARY KEY ("id")
      )`,
    );

    // Add indexes for better query performance
    await queryRunner.query(
      `CREATE INDEX "IDX_agent_user_id" ON "metadata"."agent"("userId")`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_agent_tool_agent_id" ON "metadata"."agent_tool"("agentId")`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_agent_tool_tool_id" ON "metadata"."agent_tool"("toolId")`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_user_custom_tool_configuration_user_id" ON "metadata"."user_custom_tool_configuration"("userId")`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_user_custom_tool_configuration_tool_id" ON "metadata"."user_custom_tool_configuration"("toolId")`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Drop indexes
    await queryRunner.query(`DROP INDEX "metadata"."IDX_user_custom_tool_configuration_tool_id"`);
    await queryRunner.query(`DROP INDEX "metadata"."IDX_user_custom_tool_configuration_user_id"`);
    await queryRunner.query(`DROP INDEX "metadata"."IDX_agent_tool_tool_id"`);
    await queryRunner.query(`DROP INDEX "metadata"."IDX_agent_tool_agent_id"`);
    await queryRunner.query(`DROP INDEX "metadata"."IDX_agent_user_id"`);

    // Drop tables in reverse order of creation
    await queryRunner.query(`DROP TABLE "metadata"."user_custom_tool_configuration"`);
    await queryRunner.query(`DROP TABLE "metadata"."agent_tool"`);
    await queryRunner.query(`DROP TABLE "metadata"."tool"`);
    await queryRunner.query(`DROP TABLE "metadata"."agent"`);
  }
} 
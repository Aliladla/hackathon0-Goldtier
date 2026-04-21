import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import nodemailer from 'nodemailer';
import dotenv from 'dotenv';

dotenv.config();

// Email MCP Server for Personal AI Employee
class EmailMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'ai-employee-email-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Configure SMTP transporter
    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT || '587'),
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASSWORD,
      },
    });

    this.setupHandlers();
  }

  setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'send_email',
          description: 'Send an email via Gmail SMTP',
          inputSchema: {
            type: 'object',
            properties: {
              to: {
                type: 'string',
                description: 'Recipient email address',
              },
              subject: {
                type: 'string',
                description: 'Email subject',
              },
              body: {
                type: 'string',
                description: 'Email body (plain text or HTML)',
              },
              reply_to_message_id: {
                type: 'string',
                description: 'Optional: Gmail message ID to reply to',
              },
            },
            required: ['to', 'subject', 'body'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (request.params.name === 'send_email') {
        return await this.handleSendEmail(request.params.arguments);
      }

      throw new Error(`Unknown tool: ${request.params.name}`);
    });
  }

  async handleSendEmail(args) {
    try {
      const { to, subject, body, reply_to_message_id } = args;

      // Validate inputs
      if (!to || !subject || !body) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: 'Missing required fields: to, subject, body',
              }),
            },
          ],
        };
      }

      // Prepare email options
      const mailOptions = {
        from: process.env.SMTP_USER,
        to: to,
        subject: subject,
        text: body,
      };

      // Add reply headers if replying to a message
      if (reply_to_message_id) {
        mailOptions.inReplyTo = reply_to_message_id;
        mailOptions.references = reply_to_message_id;
      }

      // Send email
      const info = await this.transporter.sendMail(mailOptions);

      console.log(`Email sent: ${info.messageId}`);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              message_id: info.messageId,
              timestamp: new Date().toISOString(),
              to: to,
              subject: subject,
            }),
          },
        ],
      };
    } catch (error) {
      console.error('Error sending email:', error);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
            }),
          },
        ],
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Email MCP Server running on stdio');
  }
}

// Start server
const server = new EmailMCPServer();
server.run().catch(console.error);

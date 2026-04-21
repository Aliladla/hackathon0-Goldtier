#!/usr/bin/env node

/**
 * Odoo MCP Server
 *
 * Provides Model Context Protocol tools for Odoo ERP integration.
 * Enables Claude Code to interact with Odoo for invoicing, payments, and financial queries.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import Odoo from 'odoo-xmlrpc';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Odoo configuration
const ODOO_URL = process.env.ODOO_URL;
const ODOO_DB = process.env.ODOO_DB;
const ODOO_USERNAME = process.env.ODOO_USERNAME;
const ODOO_PASSWORD = process.env.ODOO_PASSWORD;

// Validate configuration
if (!ODOO_URL || !ODOO_DB || !ODOO_USERNAME || !ODOO_PASSWORD) {
  console.error('ERROR: Missing Odoo configuration in .env file');
  console.error('Required: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD');
  process.exit(1);
}

// Initialize Odoo client
const odoo = new Odoo({
  url: ODOO_URL,
  db: ODOO_DB,
  username: ODOO_USERNAME,
  password: ODOO_PASSWORD,
});

// Authentication state
let uid = null;

/**
 * Authenticate with Odoo
 * @returns {Promise<number>} User ID
 */
async function authenticate() {
  if (uid) return uid;

  return new Promise((resolve, reject) => {
    odoo.connect((err, result) => {
      if (err) {
        reject(new Error(`Odoo authentication failed: ${err.message}`));
      } else {
        uid = result;
        console.error(`Authenticated with Odoo as user ${uid}`);
        resolve(uid);
      }
    });
  });
}

/**
 * Execute Odoo method with retry logic
 * @param {string} model - Odoo model name
 * @param {string} method - Method to execute
 * @param {Array} params - Method parameters
 * @param {number} retries - Number of retries
 * @returns {Promise<any>} Result
 */
async function executeWithRetry(model, method, params, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await authenticate();

      return await new Promise((resolve, reject) => {
        odoo.execute_kw(model, method, params, (err, result) => {
          if (err) {
            reject(new Error(`Odoo ${method} failed: ${err.message}`));
          } else {
            resolve(result);
          }
        });
      });
    } catch (error) {
      if (attempt === retries) {
        throw error;
      }

      // Exponential backoff
      const delay = Math.pow(2, attempt - 1) * 1000;
      console.error(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));

      // Reset authentication on error
      uid = null;
    }
  }
}

/**
 * Create invoice in Odoo
 * @param {Object} invoiceData - Invoice details
 * @returns {Promise<Object>} Created invoice
 */
async function createInvoice(invoiceData) {
  const {
    partner_name,
    partner_email,
    invoice_lines,
    payment_term_days = 30,
    date_invoice,
  } = invoiceData;

  // Find or create partner
  const partnerIds = await executeWithRetry('res.partner', 'search', [
    [['name', '=', partner_name]],
  ]);

  let partnerId;
  if (partnerIds.length > 0) {
    partnerId = partnerIds[0];
  } else {
    // Create new partner
    partnerId = await executeWithRetry('res.partner', 'create', [
      {
        name: partner_name,
        email: partner_email,
        customer_rank: 1,
      },
    ]);
  }

  // Find payment term
  const paymentTermIds = await executeWithRetry('account.payment.term', 'search', [
    [['name', 'ilike', `${payment_term_days} days`]],
  ]);

  // Prepare invoice lines
  const lines = invoice_lines.map(line => [0, 0, {
    name: line.description,
    quantity: line.quantity || 1,
    price_unit: line.unit_price,
    account_id: line.account_id || null,
  }]);

  // Create invoice
  const invoiceId = await executeWithRetry('account.move', 'create', [
    {
      partner_id: partnerId,
      move_type: 'out_invoice',
      invoice_date: date_invoice || new Date().toISOString().split('T')[0],
      invoice_payment_term_id: paymentTermIds.length > 0 ? paymentTermIds[0] : null,
      invoice_line_ids: lines,
    },
  ]);

  // Read created invoice
  const invoice = await executeWithRetry('account.move', 'read', [
    [invoiceId],
    ['name', 'partner_id', 'amount_total', 'state', 'invoice_date', 'invoice_date_due'],
  ]);

  return invoice[0];
}

/**
 * Record payment in Odoo
 * @param {Object} paymentData - Payment details
 * @returns {Promise<Object>} Recorded payment
 */
async function recordPayment(paymentData) {
  const {
    invoice_number,
    amount,
    payment_date,
    payment_method = 'manual',
    memo,
  } = paymentData;

  // Find invoice by number
  const invoiceIds = await executeWithRetry('account.move', 'search', [
    [['name', '=', invoice_number], ['move_type', '=', 'out_invoice']],
  ]);

  if (invoiceIds.length === 0) {
    throw new Error(`Invoice ${invoice_number} not found`);
  }

  const invoiceId = invoiceIds[0];

  // Find payment journal
  const journalIds = await executeWithRetry('account.journal', 'search', [
    [['type', 'in', ['bank', 'cash']]],
  ]);

  if (journalIds.length === 0) {
    throw new Error('No payment journal found');
  }

  // Create payment
  const paymentId = await executeWithRetry('account.payment', 'create', [
    {
      payment_type: 'inbound',
      partner_type: 'customer',
      amount: amount,
      date: payment_date || new Date().toISOString().split('T')[0],
      journal_id: journalIds[0],
      ref: memo || `Payment for ${invoice_number}`,
    },
  ]);

  // Post payment
  await executeWithRetry('account.payment', 'action_post', [[paymentId]]);

  // Reconcile with invoice
  const payment = await executeWithRetry('account.payment', 'read', [
    [paymentId],
    ['name', 'amount', 'date', 'state', 'move_id'],
  ]);

  // Get move lines for reconciliation
  const paymentMoveId = payment[0].move_id[0];
  const paymentLineIds = await executeWithRetry('account.move.line', 'search', [
    [['move_id', '=', paymentMoveId], ['account_id.internal_type', '=', 'receivable']],
  ]);

  const invoiceLineIds = await executeWithRetry('account.move.line', 'search', [
    [['move_id', '=', invoiceId], ['account_id.internal_type', '=', 'receivable']],
  ]);

  // Reconcile
  if (paymentLineIds.length > 0 && invoiceLineIds.length > 0) {
    await executeWithRetry('account.move.line', 'reconcile', [
      [...paymentLineIds, ...invoiceLineIds],
    ]);
  }

  return payment[0];
}

/**
 * Query financial data from Odoo
 * @param {Object} queryParams - Query parameters
 * @returns {Promise<Object>} Financial data
 */
async function queryFinancials(queryParams) {
  const {
    report_type = 'summary',
    date_from,
    date_to,
    partner_id,
  } = queryParams;

  const domain = [];
  if (date_from) domain.push(['date', '>=', date_from]);
  if (date_to) domain.push(['date', '<=', date_to]);
  if (partner_id) domain.push(['partner_id', '=', partner_id]);

  if (report_type === 'invoices') {
    // Query invoices
    const invoices = await executeWithRetry('account.move', 'search_read', [
      [...domain, ['move_type', '=', 'out_invoice']],
      ['name', 'partner_id', 'invoice_date', 'amount_total', 'state', 'payment_state'],
    ]);

    return {
      report_type: 'invoices',
      count: invoices.length,
      total_amount: invoices.reduce((sum, inv) => sum + inv.amount_total, 0),
      invoices,
    };
  } else if (report_type === 'payments') {
    // Query payments
    const payments = await executeWithRetry('account.payment', 'search_read', [
      [...domain, ['payment_type', '=', 'inbound']],
      ['name', 'partner_id', 'date', 'amount', 'state'],
    ]);

    return {
      report_type: 'payments',
      count: payments.length,
      total_amount: payments.reduce((sum, pay) => sum + pay.amount, 0),
      payments,
    };
  } else {
    // Summary report
    const invoices = await executeWithRetry('account.move', 'search_read', [
      [...domain, ['move_type', '=', 'out_invoice']],
      ['amount_total', 'state', 'payment_state'],
    ]);

    const payments = await executeWithRetry('account.payment', 'search_read', [
      [...domain, ['payment_type', '=', 'inbound']],
      ['amount'],
    ]);

    return {
      report_type: 'summary',
      period: { date_from, date_to },
      invoices: {
        count: invoices.length,
        total: invoices.reduce((sum, inv) => sum + inv.amount_total, 0),
        paid: invoices.filter(inv => inv.payment_state === 'paid').length,
        unpaid: invoices.filter(inv => inv.payment_state !== 'paid').length,
      },
      payments: {
        count: payments.length,
        total: payments.reduce((sum, pay) => sum + pay.amount, 0),
      },
    };
  }
}

/**
 * Sync transactions between vault and Odoo
 * @param {Object} syncParams - Sync parameters
 * @returns {Promise<Object>} Sync results
 */
async function syncTransactions(syncParams) {
  const {
    direction = 'bidirectional',
    date_from,
    date_to,
  } = syncParams;

  const results = {
    direction,
    synced_invoices: 0,
    synced_payments: 0,
    errors: [],
  };

  if (direction === 'from_odoo' || direction === 'bidirectional') {
    // Sync from Odoo to vault
    try {
      const domain = [];
      if (date_from) domain.push(['date', '>=', date_from]);
      if (date_to) domain.push(['date', '<=', date_to]);

      const invoices = await executeWithRetry('account.move', 'search_read', [
        [...domain, ['move_type', '=', 'out_invoice']],
        ['name', 'partner_id', 'invoice_date', 'amount_total', 'state'],
      ]);

      results.synced_invoices = invoices.length;
    } catch (error) {
      results.errors.push(`Invoice sync error: ${error.message}`);
    }
  }

  if (direction === 'to_odoo' || direction === 'bidirectional') {
    // Sync from vault to Odoo (placeholder - actual implementation would read vault files)
    results.synced_payments = 0;
  }

  return results;
}

// Create MCP server
const server = new Server(
  {
    name: 'odoo-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'create_invoice',
        description: 'Create a new invoice in Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            partner_name: {
              type: 'string',
              description: 'Customer name',
            },
            partner_email: {
              type: 'string',
              description: 'Customer email',
            },
            invoice_lines: {
              type: 'array',
              description: 'Invoice line items',
              items: {
                type: 'object',
                properties: {
                  description: { type: 'string' },
                  quantity: { type: 'number' },
                  unit_price: { type: 'number' },
                },
                required: ['description', 'unit_price'],
              },
            },
            payment_term_days: {
              type: 'number',
              description: 'Payment terms in days (default: 30)',
            },
            date_invoice: {
              type: 'string',
              description: 'Invoice date (YYYY-MM-DD)',
            },
          },
          required: ['partner_name', 'invoice_lines'],
        },
      },
      {
        name: 'record_payment',
        description: 'Record a payment for an invoice in Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            invoice_number: {
              type: 'string',
              description: 'Invoice number (e.g., INV/2026/0001)',
            },
            amount: {
              type: 'number',
              description: 'Payment amount',
            },
            payment_date: {
              type: 'string',
              description: 'Payment date (YYYY-MM-DD)',
            },
            payment_method: {
              type: 'string',
              description: 'Payment method (manual, bank, etc.)',
            },
            memo: {
              type: 'string',
              description: 'Payment memo/reference',
            },
          },
          required: ['invoice_number', 'amount'],
        },
      },
      {
        name: 'query_financials',
        description: 'Query financial data from Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            report_type: {
              type: 'string',
              enum: ['summary', 'invoices', 'payments'],
              description: 'Type of financial report',
            },
            date_from: {
              type: 'string',
              description: 'Start date (YYYY-MM-DD)',
            },
            date_to: {
              type: 'string',
              description: 'End date (YYYY-MM-DD)',
            },
            partner_id: {
              type: 'number',
              description: 'Filter by partner ID',
            },
          },
        },
      },
      {
        name: 'sync_transactions',
        description: 'Sync transactions between vault and Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            direction: {
              type: 'string',
              enum: ['from_odoo', 'to_odoo', 'bidirectional'],
              description: 'Sync direction',
            },
            date_from: {
              type: 'string',
              description: 'Start date (YYYY-MM-DD)',
            },
            date_to: {
              type: 'string',
              description: 'End date (YYYY-MM-DD)',
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'create_invoice': {
        const invoice = await createInvoice(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(invoice, null, 2),
            },
          ],
        };
      }

      case 'record_payment': {
        const payment = await recordPayment(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(payment, null, 2),
            },
          ],
        };
      }

      case 'query_financials': {
        const financials = await queryFinancials(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(financials, null, 2),
            },
          ],
        };
      }

      case 'sync_transactions': {
        const results = await syncTransactions(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Odoo MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

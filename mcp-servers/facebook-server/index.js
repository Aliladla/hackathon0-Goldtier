#!/usr/bin/env node

/**
 * Facebook MCP Server
 *
 * Provides Model Context Protocol tools for Facebook integration.
 * Enables Claude Code to create posts and collect engagement metrics.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Facebook configuration
const FACEBOOK_PAGE_ACCESS_TOKEN = process.env.FACEBOOK_PAGE_ACCESS_TOKEN;
const FACEBOOK_PAGE_ID = process.env.FACEBOOK_PAGE_ID;
const FACEBOOK_API_VERSION = process.env.FACEBOOK_API_VERSION || 'v18.0';

// Validate configuration
if (!FACEBOOK_PAGE_ACCESS_TOKEN || !FACEBOOK_PAGE_ID) {
  console.error('ERROR: Missing Facebook configuration in .env file');
  console.error('Required: FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID');
  process.exit(1);
}

// Rate limiting
const rateLimiter = {
  requests: [],
  maxRequests: 200, // Facebook Graph API limit
  windowMs: 3600000, // 1 hour

  canMakeRequest() {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.windowMs);
    return this.requests.length < this.maxRequests;
  },

  recordRequest() {
    this.requests.push(Date.now());
  },

  async waitIfNeeded() {
    if (!this.canMakeRequest()) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (Date.now() - oldestRequest);
      console.error(`Rate limit reached, waiting ${Math.ceil(waitTime / 1000)}s`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
};

/**
 * Make Facebook Graph API request with retry logic
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @param {number} retries - Number of retries
 * @returns {Promise<Object>} Response data
 */
async function makeGraphRequest(endpoint, options = {}, retries = 3) {
  await rateLimiter.waitIfNeeded();

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      rateLimiter.recordRequest();

      const url = `https://graph.facebook.com/${FACEBOOK_API_VERSION}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      if (attempt === retries) {
        throw error;
      }

      // Exponential backoff
      const delay = Math.pow(2, attempt - 1) * 1000;
      console.error(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

/**
 * Create Facebook post
 * @param {Object} postData - Post details
 * @returns {Promise<Object>} Created post
 */
async function createPost(postData) {
  const { message, link, image_url, scheduled_publish_time } = postData;

  const params = new URLSearchParams({
    access_token: FACEBOOK_PAGE_ACCESS_TOKEN,
    message: message,
  });

  if (link) {
    params.append('link', link);
  }

  if (image_url) {
    params.append('url', image_url);
  }

  if (scheduled_publish_time) {
    params.append('published', 'false');
    params.append('scheduled_publish_time', scheduled_publish_time);
  }

  const endpoint = `/${FACEBOOK_PAGE_ID}/feed`;
  const data = await makeGraphRequest(endpoint, {
    method: 'POST',
    body: params,
  });

  return {
    id: data.id,
    post_id: data.id,
    message: message,
    created_time: new Date().toISOString(),
    scheduled: !!scheduled_publish_time,
  };
}

/**
 * Get post insights (engagement metrics)
 * @param {Object} insightsParams - Insights parameters
 * @returns {Promise<Object>} Post insights
 */
async function getPostInsights(insightsParams) {
  const { post_id, metrics } = insightsParams;

  const metricsToFetch = metrics || [
    'post_impressions',
    'post_impressions_unique',
    'post_engaged_users',
    'post_clicks',
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total',
  ];

  const params = new URLSearchParams({
    access_token: FACEBOOK_PAGE_ACCESS_TOKEN,
    metric: metricsToFetch.join(','),
  });

  const endpoint = `/${post_id}/insights?${params}`;
  const data = await makeGraphRequest(endpoint);

  // Parse insights data
  const insights = {};
  if (data.data) {
    for (const metric of data.data) {
      insights[metric.name] = metric.values[0]?.value || 0;
    }
  }

  // Get post details
  const postParams = new URLSearchParams({
    access_token: FACEBOOK_PAGE_ACCESS_TOKEN,
    fields: 'message,created_time,shares,comments.summary(true),reactions.summary(true)',
  });

  const postEndpoint = `/${post_id}?${postParams}`;
  const postData = await makeGraphRequest(postEndpoint);

  return {
    post_id: post_id,
    message: postData.message,
    created_time: postData.created_time,
    insights: insights,
    engagement: {
      shares: postData.shares?.count || 0,
      comments: postData.comments?.summary?.total_count || 0,
      reactions: postData.reactions?.summary?.total_count || 0,
    },
  };
}

/**
 * Delete post
 * @param {string} post_id - Post ID
 * @returns {Promise<Object>} Deletion result
 */
async function deletePost(post_id) {
  const params = new URLSearchParams({
    access_token: FACEBOOK_PAGE_ACCESS_TOKEN,
  });

  const endpoint = `/${post_id}?${params}`;
  const data = await makeGraphRequest(endpoint, {
    method: 'DELETE',
  });

  return {
    success: data.success || false,
    post_id: post_id,
  };
}

// Create MCP server
const server = new Server(
  {
    name: 'facebook-server',
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
        name: 'create_post',
        description: 'Create a post on Facebook page',
        inputSchema: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'Post message/content',
            },
            link: {
              type: 'string',
              description: 'Optional link to share',
            },
            image_url: {
              type: 'string',
              description: 'Optional image URL',
            },
            scheduled_publish_time: {
              type: 'number',
              description: 'Optional Unix timestamp for scheduled post',
            },
          },
          required: ['message'],
        },
      },
      {
        name: 'get_post_insights',
        description: 'Get engagement metrics for a Facebook post',
        inputSchema: {
          type: 'object',
          properties: {
            post_id: {
              type: 'string',
              description: 'Facebook post ID',
            },
            metrics: {
              type: 'array',
              description: 'Optional list of specific metrics to fetch',
              items: {
                type: 'string',
              },
            },
          },
          required: ['post_id'],
        },
      },
      {
        name: 'delete_post',
        description: 'Delete a Facebook post',
        inputSchema: {
          type: 'object',
          properties: {
            post_id: {
              type: 'string',
              description: 'Facebook post ID to delete',
            },
          },
          required: ['post_id'],
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
      case 'create_post': {
        const post = await createPost(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(post, null, 2),
            },
          ],
        };
      }

      case 'get_post_insights': {
        const insights = await getPostInsights(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(insights, null, 2),
            },
          ],
        };
      }

      case 'delete_post': {
        const result = await deletePost(args.post_id);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
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
  console.error('Facebook MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

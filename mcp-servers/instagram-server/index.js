#!/usr/bin/env node

/**
 * Instagram MCP Server
 *
 * Provides Model Context Protocol tools for Instagram integration.
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

// Instagram configuration
const INSTAGRAM_ACCESS_TOKEN = process.env.INSTAGRAM_ACCESS_TOKEN;
const INSTAGRAM_ACCOUNT_ID = process.env.INSTAGRAM_ACCOUNT_ID;
const INSTAGRAM_API_VERSION = process.env.INSTAGRAM_API_VERSION || 'v18.0';

// Validate configuration
if (!INSTAGRAM_ACCESS_TOKEN || !INSTAGRAM_ACCOUNT_ID) {
  console.error('ERROR: Missing Instagram configuration in .env file');
  console.error('Required: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID');
  process.exit(1);
}

// Rate limiting
const rateLimiter = {
  requests: [],
  maxRequests: 200,
  windowMs: 3600000,

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
 * Make Instagram Graph API request with retry logic
 */
async function makeGraphRequest(endpoint, options = {}, retries = 3) {
  await rateLimiter.waitIfNeeded();

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      rateLimiter.recordRequest();

      const url = `https://graph.facebook.com/${INSTAGRAM_API_VERSION}${endpoint}`;
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

      const delay = Math.pow(2, attempt - 1) * 1000;
      console.error(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

/**
 * Create Instagram post (image or carousel)
 */
async function createPost(postData) {
  const { caption, image_url, media_type = 'IMAGE' } = postData;

  // Step 1: Create media container
  const containerParams = new URLSearchParams({
    access_token: INSTAGRAM_ACCESS_TOKEN,
    image_url: image_url,
    caption: caption,
    media_type: media_type,
  });

  const containerEndpoint = `/${INSTAGRAM_ACCOUNT_ID}/media`;
  const containerData = await makeGraphRequest(containerEndpoint, {
    method: 'POST',
    body: containerParams,
  });

  const containerId = containerData.id;

  // Step 2: Publish media container
  const publishParams = new URLSearchParams({
    access_token: INSTAGRAM_ACCESS_TOKEN,
    creation_id: containerId,
  });

  const publishEndpoint = `/${INSTAGRAM_ACCOUNT_ID}/media_publish`;
  const publishData = await makeGraphRequest(publishEndpoint, {
    method: 'POST',
    body: publishParams,
  });

  return {
    id: publishData.id,
    media_id: publishData.id,
    caption: caption,
    created_time: new Date().toISOString(),
    media_type: media_type,
  };
}

/**
 * Get media insights (engagement metrics)
 */
async function getMediaInsights(insightsParams) {
  const { media_id, metrics } = insightsParams;

  const metricsToFetch = metrics || [
    'impressions',
    'reach',
    'engagement',
    'saved',
    'likes',
    'comments',
    'shares',
  ];

  const params = new URLSearchParams({
    access_token: INSTAGRAM_ACCESS_TOKEN,
    metric: metricsToFetch.join(','),
  });

  const endpoint = `/${media_id}/insights?${params}`;
  const data = await makeGraphRequest(endpoint);

  // Parse insights data
  const insights = {};
  if (data.data) {
    for (const metric of data.data) {
      insights[metric.name] = metric.values[0]?.value || 0;
    }
  }

  // Get media details
  const mediaParams = new URLSearchParams({
    access_token: INSTAGRAM_ACCESS_TOKEN,
    fields: 'caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
  });

  const mediaEndpoint = `/${media_id}?${mediaParams}`;
  const mediaData = await makeGraphRequest(mediaEndpoint);

  return {
    media_id: media_id,
    caption: mediaData.caption,
    media_type: mediaData.media_type,
    permalink: mediaData.permalink,
    timestamp: mediaData.timestamp,
    insights: insights,
    engagement: {
      likes: mediaData.like_count || 0,
      comments: mediaData.comments_count || 0,
    },
  };
}

/**
 * Delete media
 */
async function deleteMedia(media_id) {
  const params = new URLSearchParams({
    access_token: INSTAGRAM_ACCESS_TOKEN,
  });

  const endpoint = `/${media_id}?${params}`;
  const data = await makeGraphRequest(endpoint, {
    method: 'DELETE',
  });

  return {
    success: data.success || false,
    media_id: media_id,
  };
}

// Create MCP server
const server = new Server(
  {
    name: 'instagram-server',
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
        description: 'Create a post on Instagram (image or carousel)',
        inputSchema: {
          type: 'object',
          properties: {
            caption: {
              type: 'string',
              description: 'Post caption (max 2200 characters)',
            },
            image_url: {
              type: 'string',
              description: 'Image URL (must be publicly accessible)',
            },
            media_type: {
              type: 'string',
              enum: ['IMAGE', 'CAROUSEL_ALBUM'],
              description: 'Media type (default: IMAGE)',
            },
          },
          required: ['caption', 'image_url'],
        },
      },
      {
        name: 'get_media_insights',
        description: 'Get engagement metrics for Instagram media',
        inputSchema: {
          type: 'object',
          properties: {
            media_id: {
              type: 'string',
              description: 'Instagram media ID',
            },
            metrics: {
              type: 'array',
              description: 'Optional list of specific metrics to fetch',
              items: {
                type: 'string',
              },
            },
          },
          required: ['media_id'],
        },
      },
      {
        name: 'delete_media',
        description: 'Delete Instagram media',
        inputSchema: {
          type: 'object',
          properties: {
            media_id: {
              type: 'string',
              description: 'Instagram media ID to delete',
            },
          },
          required: ['media_id'],
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

      case 'get_media_insights': {
        const insights = await getMediaInsights(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(insights, null, 2),
            },
          ],
        };
      }

      case 'delete_media': {
        const result = await deleteMedia(args.media_id);
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
  console.error('Instagram MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

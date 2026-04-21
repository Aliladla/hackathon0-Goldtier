#!/usr/bin/env node

/**
 * Twitter MCP Server
 *
 * Provides Model Context Protocol tools for Twitter/X integration.
 * Enables Claude Code to create tweets, threads, and collect engagement metrics.
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

// Twitter configuration
const TWITTER_API_KEY = process.env.TWITTER_API_KEY;
const TWITTER_API_SECRET = process.env.TWITTER_API_SECRET;
const TWITTER_ACCESS_TOKEN = process.env.TWITTER_ACCESS_TOKEN;
const TWITTER_ACCESS_SECRET = process.env.TWITTER_ACCESS_SECRET;
const TWITTER_BEARER_TOKEN = process.env.TWITTER_BEARER_TOKEN;

// Validate configuration
if (!TWITTER_BEARER_TOKEN || !TWITTER_ACCESS_TOKEN || !TWITTER_ACCESS_SECRET) {
  console.error('ERROR: Missing Twitter configuration in .env file');
  console.error('Required: TWITTER_BEARER_TOKEN, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET');
  process.exit(1);
}

// Rate limiting
const rateLimiter = {
  requests: [],
  maxRequests: 300, // Twitter API v2 limit
  windowMs: 900000, // 15 minutes

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
 * Generate OAuth 1.0a signature for Twitter API
 */
function generateOAuthHeader(method, url, params = {}) {
  const crypto = require('crypto');

  const oauthParams = {
    oauth_consumer_key: TWITTER_API_KEY,
    oauth_token: TWITTER_ACCESS_TOKEN,
    oauth_signature_method: 'HMAC-SHA1',
    oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
    oauth_nonce: crypto.randomBytes(32).toString('hex'),
    oauth_version: '1.0',
  };

  const allParams = { ...oauthParams, ...params };
  const sortedParams = Object.keys(allParams)
    .sort()
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(allParams[key])}`)
    .join('&');

  const signatureBase = `${method.toUpperCase()}&${encodeURIComponent(url)}&${encodeURIComponent(sortedParams)}`;
  const signingKey = `${encodeURIComponent(TWITTER_API_SECRET)}&${encodeURIComponent(TWITTER_ACCESS_SECRET)}`;
  const signature = crypto.createHmac('sha1', signingKey).update(signatureBase).digest('base64');

  oauthParams.oauth_signature = signature;

  const authHeader = 'OAuth ' + Object.keys(oauthParams)
    .sort()
    .map(key => `${encodeURIComponent(key)}="${encodeURIComponent(oauthParams[key])}"`)
    .join(', ');

  return authHeader;
}

/**
 * Make Twitter API request with retry logic
 */
async function makeTwitterRequest(endpoint, options = {}, retries = 3) {
  await rateLimiter.waitIfNeeded();

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      rateLimiter.recordRequest();

      const url = `https://api.twitter.com/2${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Authorization': `Bearer ${TWITTER_BEARER_TOKEN}`,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.errors?.[0]?.message || data.detail || `HTTP ${response.status}`);
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
 * Create tweet (single or thread)
 */
async function createTweet(tweetData) {
  const { text, reply_to_tweet_id, media_ids } = tweetData;

  const payload = {
    text: text,
  };

  if (reply_to_tweet_id) {
    payload.reply = {
      in_reply_to_tweet_id: reply_to_tweet_id,
    };
  }

  if (media_ids && media_ids.length > 0) {
    payload.media = {
      media_ids: media_ids,
    };
  }

  const endpoint = '/tweets';
  const data = await makeTwitterRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  return {
    id: data.data.id,
    tweet_id: data.data.id,
    text: data.data.text,
    created_at: new Date().toISOString(),
  };
}

/**
 * Create tweet thread
 */
async function createThread(threadData) {
  const { tweets } = threadData;

  if (!Array.isArray(tweets) || tweets.length === 0) {
    throw new Error('Thread must contain at least one tweet');
  }

  const createdTweets = [];
  let previousTweetId = null;

  for (const tweetText of tweets) {
    const tweet = await createTweet({
      text: tweetText,
      reply_to_tweet_id: previousTweetId,
    });

    createdTweets.push(tweet);
    previousTweetId = tweet.tweet_id;

    // Small delay between tweets to avoid rate limits
    if (previousTweetId) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  return {
    thread_id: createdTweets[0].tweet_id,
    tweets: createdTweets,
    count: createdTweets.length,
  };
}

/**
 * Get tweet metrics (engagement)
 */
async function getTweetMetrics(metricsParams) {
  const { tweet_id } = metricsParams;

  const params = new URLSearchParams({
    'tweet.fields': 'public_metrics,created_at,text',
  });

  const endpoint = `/tweets/${tweet_id}?${params}`;
  const data = await makeTwitterRequest(endpoint);

  const tweet = data.data;
  const metrics = tweet.public_metrics || {};

  return {
    tweet_id: tweet.id,
    text: tweet.text,
    created_at: tweet.created_at,
    metrics: {
      retweets: metrics.retweet_count || 0,
      replies: metrics.reply_count || 0,
      likes: metrics.like_count || 0,
      quotes: metrics.quote_count || 0,
      impressions: metrics.impression_count || 0,
    },
    engagement_rate: metrics.impression_count > 0
      ? ((metrics.like_count + metrics.retweet_count + metrics.reply_count) / metrics.impression_count * 100).toFixed(2)
      : 0,
  };
}

/**
 * Delete tweet
 */
async function deleteTweet(tweet_id) {
  const endpoint = `/tweets/${tweet_id}`;
  const data = await makeTwitterRequest(endpoint, {
    method: 'DELETE',
  });

  return {
    deleted: data.data?.deleted || false,
    tweet_id: tweet_id,
  };
}

// Create MCP server
const server = new Server(
  {
    name: 'twitter-server',
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
        name: 'create_tweet',
        description: 'Create a single tweet on Twitter/X',
        inputSchema: {
          type: 'object',
          properties: {
            text: {
              type: 'string',
              description: 'Tweet text (max 280 characters)',
            },
            reply_to_tweet_id: {
              type: 'string',
              description: 'Optional tweet ID to reply to',
            },
            media_ids: {
              type: 'array',
              description: 'Optional media IDs to attach',
              items: {
                type: 'string',
              },
            },
          },
          required: ['text'],
        },
      },
      {
        name: 'create_thread',
        description: 'Create a tweet thread on Twitter/X',
        inputSchema: {
          type: 'object',
          properties: {
            tweets: {
              type: 'array',
              description: 'Array of tweet texts (each max 280 characters)',
              items: {
                type: 'string',
              },
            },
          },
          required: ['tweets'],
        },
      },
      {
        name: 'get_tweet_metrics',
        description: 'Get engagement metrics for a tweet',
        inputSchema: {
          type: 'object',
          properties: {
            tweet_id: {
              type: 'string',
              description: 'Twitter tweet ID',
            },
          },
          required: ['tweet_id'],
        },
      },
      {
        name: 'delete_tweet',
        description: 'Delete a tweet',
        inputSchema: {
          type: 'object',
          properties: {
            tweet_id: {
              type: 'string',
              description: 'Twitter tweet ID to delete',
            },
          },
          required: ['tweet_id'],
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
      case 'create_tweet': {
        const tweet = await createTweet(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tweet, null, 2),
            },
          ],
        };
      }

      case 'create_thread': {
        const thread = await createThread(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(thread, null, 2),
            },
          ],
        };
      }

      case 'get_tweet_metrics': {
        const metrics = await getTweetMetrics(args);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(metrics, null, 2),
            },
          ],
        };
      }

      case 'delete_tweet': {
        const result = await deleteTweet(args.tweet_id);
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
  console.error('Twitter MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

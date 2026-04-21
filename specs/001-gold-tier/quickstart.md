# Gold Tier Quickstart Guide

**Feature**: 001-gold-tier  
**Date**: 2026-04-16  
**Purpose**: Setup and usage instructions for Gold tier autonomous AI employee

## Prerequisites

Before starting Gold tier setup, ensure:

1. ✅ **Bronze tier operational** - File watcher, vault structure, basic Agent Skills
2. ✅ **Silver tier operational** - Gmail, WhatsApp, LinkedIn watchers, approval workflow, scheduler
3. ✅ **Python 3.13+** installed
4. ✅ **Node.js 24+** installed
5. ✅ **Odoo Community Edition v19+** installed and accessible
6. ✅ **Social media accounts** with API access:
   - Facebook Page with admin access
   - Instagram Business Account
   - Twitter Developer Account with API v2 access

## Installation

### 1. Install Python Dependencies

```bash
# Navigate to project root
cd C:\Users\Dell\Desktop\hackathon0ali

# Install Gold tier dependencies
pip install odoorpc facebook-sdk instagrapi tweepy tenacity

# Verify installation
python -c "import odoorpc, facebook, instagrapi, tweepy, tenacity; print('All dependencies installed')"
```

### 2. Install MCP Server Dependencies

```bash
# Odoo MCP Server
cd mcp-servers/odoo-server
npm install
cd ../..

# Facebook MCP Server
cd mcp-servers/facebook-server
npm install
cd ../..

# Instagram MCP Server
cd mcp-servers/instagram-server
npm install
cd ../..

# Twitter MCP Server
cd mcp-servers/twitter-server
npm install
cd ../..
```

### 3. Configure Environment Variables

Create or update `.env` file in project root:

```bash
# Bronze/Silver tier (existing)
DRY_RUN=true
ENABLE_FILE_WATCHER=true
ENABLE_GMAIL=false
ENABLE_WHATSAPP=false
ENABLE_LINKEDIN=false
ENABLE_SCHEDULER=true
DAILY_BRIEFING_TIME=08:00

# Gold tier - Odoo
ENABLE_ODOO=true
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password

# Gold tier - Social Media
ENABLE_SOCIAL_MEDIA=true
FACEBOOK_PAGE_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_SECRET=your_secret

# Gold tier - Ralph Wiggum Loop
ENABLE_RALPH_WIGGUM=true
RALPH_MAX_ITERATIONS=10

# Gold tier - Weekly Audit
ENABLE_WEEKLY_AUDIT=true
WEEKLY_AUDIT_DAY=Sunday
WEEKLY_AUDIT_TIME=23:00
```

### 4. Create Vault Folders

```bash
# Create Gold tier vault folders
mkdir -p AI_Employee_Vault/Accounting/Invoices
mkdir -p AI_Employee_Vault/Accounting/Payments
mkdir -p AI_Employee_Vault/Accounting/Reports
mkdir -p AI_Employee_Vault/Social_Media/Drafts
mkdir -p AI_Employee_Vault/Social_Media/Published
mkdir -p AI_Employee_Vault/Social_Media/Analytics
```

### 5. Configure MCP Servers in Claude Code

Edit `~/.config/claude-code/mcp.json` (or equivalent on Windows):

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["C:/Users/Dell/Desktop/hackathon0ali/mcp-servers/email-server/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "C:/Users/Dell/Desktop/hackathon0ali/config/gmail_credentials.json"
      }
    },
    {
      "name": "odoo",
      "command": "node",
      "args": ["C:/Users/Dell/Desktop/hackathon0ali/mcp-servers/odoo-server/index.js"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "your_database_name",
        "ODOO_USERNAME": "your_username",
        "ODOO_PASSWORD": "your_password"
      }
    },
    {
      "name": "facebook",
      "command": "node",
      "args": ["C:/Users/Dell/Desktop/hackathon0ali/mcp-servers/facebook-server/index.js"],
      "env": {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "your_token",
        "FACEBOOK_PAGE_ID": "your_page_id"
      }
    },
    {
      "name": "instagram",
      "command": "node",
      "args": ["C:/Users/Dell/Desktop/hackathon0ali/mcp-servers/instagram-server/index.js"],
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "your_token",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "your_account_id"
      }
    },
    {
      "name": "twitter",
      "command": "node",
      "args": ["C:/Users/Dell/Desktop/hackathon0ali/mcp-servers/twitter-server/index.js"],
      "env": {
        "TWITTER_API_KEY": "your_key",
        "TWITTER_API_SECRET": "your_secret",
        "TWITTER_ACCESS_TOKEN": "your_token",
        "TWITTER_ACCESS_SECRET": "your_secret"
      }
    }
  ]
}
```

## Odoo Setup

### 1. Install Odoo Community Edition

```bash
# Download Odoo 19 Community Edition
# https://www.odoo.com/page/download

# Install and start Odoo
# Follow official installation guide for your OS
```

### 2. Configure Odoo Database

1. Create new database via Odoo web interface (http://localhost:8069)
2. Install required modules:
   - Accounting (account)
   - Invoicing (account_invoicing)
   - Contacts (contacts)
3. Create API user:
   - Settings → Users → Create
   - Username: api_user
   - Access Rights: Accounting / Manager
4. Configure chart of accounts (if not auto-configured)

### 3. Test Odoo Connection

```python
# Test script: test_odoo_connection.py
import odoorpc

odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('your_database', 'your_username', 'your_password')

# Test query
partners = odoo.env['res.partner'].search([])
print(f"Connected! Found {len(partners)} contacts.")
```

## Social Media API Setup

### Facebook

1. Go to https://developers.facebook.com/
2. Create new app → Business type
3. Add Facebook Login product
4. Add Pages API product
5. Generate Page Access Token:
   - Tools → Graph API Explorer
   - Select your page
   - Get Token → Get Page Access Token
   - Grant permissions: pages_manage_posts, pages_read_engagement
6. Copy token to `.env`

### Instagram

1. Convert Instagram account to Business Account (via Facebook Page)
2. Go to https://developers.facebook.com/
3. Use same app as Facebook
4. Add Instagram Graph API product
5. Generate Access Token:
   - Tools → Graph API Explorer
   - Select Instagram Business Account
   - Grant permissions: instagram_basic, instagram_content_publish
6. Get Instagram Business Account ID:
   - Query: `me/accounts` → get page ID
   - Query: `{page_id}?fields=instagram_business_account`
7. Copy token and account ID to `.env`

### Twitter

1. Go to https://developer.twitter.com/
2. Create new project and app
3. Enable OAuth 2.0
4. Generate API keys and tokens:
   - Keys and tokens tab
   - Generate API Key and Secret
   - Generate Access Token and Secret
5. Grant permissions: Read and Write
6. Copy all credentials to `.env`

## Running Gold Tier

### Development Mode (Dry Run)

```bash
# Start with DRY_RUN=true (no real external actions)
python src/main.py

# You should see:
# ============================================================
# Personal AI Employee (Gold Tier) Starting
# ============================================================
# Starting Bronze Tier Components
# ✓ File Watcher started
# Starting Silver Tier Components
# ✓ Approval Orchestrator started
# ✓ Gmail Watcher started (if enabled)
# ✓ WhatsApp Watcher started (if enabled)
# ✓ LinkedIn Watcher started (if enabled)
# ✓ Scheduler started
# Starting Gold Tier Components
# ✓ Ralph Wiggum Loop started
# ✓ Odoo Integration started
# ✓ Social Media Integration started
# ✓ Audit Orchestrator started
# ✓ Watchdog started
# ============================================================
```

### Production Mode

```bash
# After testing, enable real actions
# Edit .env: DRY_RUN=false

# Start with process manager for 24/7 operation
pm2 start src/main.py --name ai-employee --interpreter python3

# Monitor logs
pm2 logs ai-employee

# Check status
pm2 status

# Stop
pm2 stop ai-employee
```

## Usage Examples

### Example 1: Autonomous Invoice Processing

1. **Create invoice file** in `AI_Employee_Vault/Needs_Action/INVOICE_client_a.md`:

```markdown
---
type: invoice
customer: Client A
amount: 1500.00
due_date: 2026-05-01
status: pending
---

## Invoice Details
- Service: Web Development
- Hours: 30
- Rate: $50/hour
- Total: $1,500.00

## Action Required
Create invoice in Odoo and send to client via email.
```

2. **Ralph Wiggum loop processes**:
   - Reads invoice file
   - Creates invoice in Odoo via MCP
   - Drafts email with invoice attached
   - Creates approval request in Pending_Approval/
   - Waits for approval
   - Sends email when approved
   - Moves task to Done/
   - Logs all actions

3. **Check results**:
   - Invoice in Odoo: http://localhost:8069/web#action=account.action_move_out_invoice_type
   - Email sent (check Gmail)
   - Task in Done/ folder
   - Log entry in Logs/YYYY-MM-DD.json

### Example 2: Social Media Post

1. **Create business update** in `AI_Employee_Vault/Business_Updates/new_feature.md`:

```markdown
---
title: New Feature Launch
date: 2026-04-16
---

We're excited to announce our new AI-powered analytics dashboard! 
This feature helps businesses make data-driven decisions faster.

Key benefits:
- Real-time insights
- Automated reporting
- Predictive analytics

Learn more: https://example.com/new-feature
```

2. **AI processes**:
   - Detects new business update
   - Generates platform-specific posts:
     - Facebook: Detailed post with link
     - Instagram: Visual-focused with hashtags
     - Twitter: Concise with thread
   - Creates approval requests
   - Publishes when approved
   - Collects engagement metrics after 24 hours

3. **Check results**:
   - Posts on all platforms
   - Drafts in Social_Media/Drafts/
   - Published posts in Social_Media/Published/
   - Engagement report in Social_Media/Analytics/

### Example 3: Weekly CEO Briefing

1. **Automatic trigger**: Every Sunday 11:00 PM

2. **AI generates briefing**:
   - Queries Odoo for weekly financials
   - Analyzes completed tasks
   - Collects social media engagement
   - Identifies cost optimizations
   - Generates recommendations

3. **Check results**:
   - Briefing in `Briefings/2026-04-21_weekly_briefing.md`
   - Dashboard.md updated with link
   - Email notification (optional)

## Troubleshooting

### Odoo Connection Failed

```bash
# Check Odoo is running
curl http://localhost:8069

# Test credentials
python test_odoo_connection.py

# Check firewall settings
# Ensure port 8069 is accessible
```

### Social Media API Errors

```bash
# Check token validity
# Facebook: https://developers.facebook.com/tools/debug/accesstoken/
# Instagram: Same as Facebook
# Twitter: https://developer.twitter.com/en/portal/dashboard

# Regenerate tokens if expired
# Update .env with new tokens
# Restart system
```

### Ralph Wiggum Loop Not Completing

```bash
# Check logs
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep ralph_wiggum

# Check iteration count
# If max iterations reached, task moved to Errors/

# Review task file for issues
# Fix and move back to Needs_Action/
```

### MCP Server Not Responding

```bash
# Check MCP server logs
pm2 logs odoo-server
pm2 logs facebook-server

# Restart MCP server
pm2 restart odoo-server

# Test MCP server directly
node mcp-servers/odoo-server/index.js
```

## Monitoring

### Dashboard

Check `AI_Employee_Vault/Dashboard.md` for real-time status:
- Active tasks
- Recent completions
- Pending approvals
- System health
- Latest briefing link

### Logs

```bash
# View today's logs
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq

# Search for errors
cat AI_Employee_Vault/Logs/*.json | jq 'select(.error_type != null)'

# Count actions by type
cat AI_Employee_Vault/Logs/*.json | jq -r '.action_type' | sort | uniq -c
```

### Health Checks

```bash
# Check all components
pm2 status

# Check MCP servers
curl http://localhost:3000/health  # Adjust ports as needed

# Check Odoo
curl http://localhost:8069/web/health
```

## Security Best Practices

1. **Never commit .env file** - Already in .gitignore
2. **Rotate credentials monthly** - Set calendar reminder
3. **Review logs weekly** - Check for suspicious activity
4. **Backup vault daily** - Use git or file backup
5. **Test in dry-run first** - Always test with DRY_RUN=true
6. **Monitor rate limits** - Check platform dashboards
7. **Review approvals promptly** - Don't let approvals expire

## Next Steps

1. ✅ Complete Gold tier setup
2. ✅ Test each component individually
3. ✅ Run in dry-run mode for 1 week
4. ✅ Enable production mode
5. ✅ Monitor for 1 week
6. ✅ Optimize based on usage patterns
7. 🎯 Consider Platinum tier (cloud deployment)

## Support

- **Documentation**: See specs/001-gold-tier/ for detailed architecture
- **Issues**: Create issue in GitHub repository
- **Community**: Join Wednesday research meetings (Zoom link in hackathon doc)

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-16  
**Status**: Ready for implementation

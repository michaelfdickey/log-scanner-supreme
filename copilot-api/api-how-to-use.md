# GitHub Copilot API Integration Guide

## Overview
This document describes how to successfully integrate with the GitHub Copilot API for chat completions, based on our working implementation in Dr. Arctopus.

## API Endpoint
```
POST https://api.githubcopilot.com/chat/completions
```

## Authentication
You need a GitHub Personal Access Token (PAT) with Copilot access. The API supports both classic and fine-grained tokens:
- Classic tokens: `ghp_...`
- Fine-grained tokens: `github_pat_...`

## Required Headers
The following headers are **required** for successful API calls:

```http
Authorization: Bearer YOUR_GITHUB_PAT
Content-Type: application/json
Accept: application/json
Copilot-Integration-Id: copilot-chat
```

### Critical Notes:
- `Copilot-Integration-Id` must be exactly `copilot-chat` (other values like `copilot-embedded-experience` may also work)
- Do NOT include `X-GitHub-Api-Version` header (causes 400 errors)
- Additional X- headers (like `X-Interaction-ID`, `X-Initiator`, etc.) are optional and may cause issues

## Request Body Structure
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Your message here"
    }
  ]
}
```

## Complete cURL Example
```bash
curl -X POST https://api.githubcopilot.com/chat/completions \
  -H "Authorization: Bearer YOUR_GITHUB_PAT" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Copilot-Integration-Id: copilot-chat" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello! This is a test message."
      }
    ]
  }'
```

## Successful Response Structure
```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "content_filter_results": {
        "hate": {
          "filtered": false,
          "severity": "safe"
        },
        "self_harm": {
          "filtered": false,
          "severity": "safe"
        },
        "sexual": {
          "filtered": false,
          "severity": "safe"
        },
        "violence": {
          "filtered": false,
          "severity": "safe"
        }
      },
      "message": {
        "content": "Hello! Your test message has been received. The connection is working. How can I assist you further?",
        "padding": "abcdefghijklmnopqrstuvwxyz01",
        "role": "assistant"
      }
    }
  ],
  "id": "chatcmpl-CZOgL44stkaFnveVD6lnZYEygdajk",
  "usage": {
    "completion_tokens": 22,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens": 31,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "total_tokens": 53
  },
  "model": "gpt-4o-mini-2024-07-18",
  "prompt_filter_results": [
    {
      "content_filter_results": {
        "hate": {
          "filtered": false,
          "severity": "safe"
        },
        "self_harm": {
          "filtered": false,
          "severity": "safe"
        },
        "sexual": {
          "filtered": false,
          "severity": "safe"
        },
        "violence": {
          "filtered": false,
          "severity": "safe"
        }
      },
      "prompt_index": 0
    }
  ],
  "system_fingerprint": "fp_efad92c60b"
}
```

## Common Error Responses

### 400 Bad Request - Invalid Integration ID
```json
{
  "error": "bad request: unknown Copilot-Integration-Id"
}
```
**Solution**: Use `Copilot-Integration-Id: copilot-chat`

### 400 Bad Request - Invalid API Version
```json
{
  "error": "bad request: error: invalid apiVersion"
}
```
**Solution**: Remove `X-GitHub-Api-Version` header entirely

### 401 Unauthorized
```json
{
  "error": "Unauthorized"
}
```
**Solution**: Check your PAT has Copilot access and is correctly formatted

## Python Implementation Example
```python
import requests
import json

def call_copilot_api(token, message):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Copilot-Integration-Id': 'copilot-chat'
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }
    
    response = requests.post(
        'https://api.githubcopilot.com/chat/completions',
        headers=headers,
        json=data,
        verify=True,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")
```

## JavaScript/Browser Limitations
- **CORS Issues**: The Copilot API does not allow direct browser requests due to CORS restrictions
- **Solution**: Use a server-side proxy (like our Python server.py implementation)
- **SSL Certificates**: Some environments may have SSL verification issues; handle appropriately

## Working Implementation
See our `server.py` file for a complete working implementation that handles:
- SSL certificate verification
- Proper error handling and logging
- CORS headers for browser integration
- Token validation and storage

## Rate Limits
- The API has rate limits (exact limits not documented)
- Handle 429 responses appropriately with exponential backoff
- Consider caching responses for repeated queries

## Security Best Practices
- Store PATs securely (use environment variables in production)
- Never expose PATs in client-side code
- Use HTTPS for all API communications
- Validate and sanitize user input before sending to API

---
*Last updated: November 7, 2025*
*Based on successful implementation in Dr. Arctopus log analyzer*

  -----------


Picking a model
The /models endpoint advertises the Copilot models that can be used with the Responses API. Each model includes a supported_endpoints array. Models that contain the value "/responses" are available to use on this endpoint.

{
  "id": "gpt-5-codex",
  "capabilities": {
    "type": "chat"
  },
  "supported_endpoints": [
    "/chat/completions",
    "/responses"
  ]
}
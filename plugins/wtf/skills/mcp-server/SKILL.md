---
name: mcp-server
description: Use when adding, connecting, verifying, or debugging an MCP (Model Context Protocol) server - wiring Claude to a tool server, confirming it actually responds, testing a tool's contract before trusting it, or diagnosing why a server the config says is there shows up empty. Covers stdio and Streamable HTTP transports, the initialize handshake, tools/list, and the registry manifest pattern.
department: engineering
---

# MCP Server — Connect, Verify, Trust Nothing

## Overview

**Core principle:** A server listed in a config file is a *claim*, not a fact. Until you have seen `tools/list` return real tool names from that server, nothing is connected.

MCP is a client/server protocol: the **client** (Claude Desktop, Claude Code, or any MCP host) launches or connects to a **server**, the server advertises **tools** (and prompts/resources), and the client calls them. Two transports matter:

- **stdio** — client spawns a local process, speaks JSON-RPC over stdin/stdout. Default for local tools.
- **Streamable HTTP** — client POSTs to a URL. Used for remote/hosted servers.

## The Iron Law

```
NO "IT SHOULD BE CONNECTED" WITHOUT A LIVE tools/list RESPONSE
```

Config files are not evidence. A server that fails to spawn, fails auth, or returns an empty tool list is *not* connected, no matter what the JSON says.

## The Gate Function

```
BEFORE trusting any MCP server:

1. READ:    What transport? What command or URL?
2. SPAWN:   Can the client actually start it / reach it?
3. SHAKE:   Did the initialize handshake complete?
4. LIST:    Did tools/list return real names (not [])?
5. CALL:    Did one real tool call return a usable payload?
6. ONLY THEN: treat the server as live
```

Skip a step and you will debug a phantom connection for an hour.

## Step 1 — Register the server

**Local (stdio), Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent per-platform path:

```json
{
  "mcpServers": {
    "tipmaster-consensus": {
      "command": "npx",
      "args": ["-y", "@example/server"]
    }
  }
}
```

**Remote (Streamable HTTP), no auth:**

```json
{
  "mcpServers": {
    "tipmaster-consensus": { "url": "https://example.net/api/agent/mcp" }
  }
}
```

**Claude Code** — use the CLI, not hand-edited JSON:

```bash
claude mcp add <name> --transport http <url>
claude mcp add <name> --transport stdio <command> -- <args...>
claude mcp list          # what is actually registered
claude mcp get <name>    # resolved config for one server
```

`claude mcp list` showing a server is still not proof it works — it only proves the config parsed.

## Step 2 — Verify the handshake and the tool list

The only real test is seeing tools come back. Two ways:

**From Claude Code**, after registering:

```
/mcp
```

lists connected servers and their tools. If a server appears with zero tools, it registered but did not load.

**From the shell**, against a remote server:

```bash
curl -s -X POST https://example.net/api/agent/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}'
```

Then `tools/list`:

```bash
curl -s -X POST https://example.net/api/agent/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Streamable HTTP servers return either `application/json` or `text/event-stream`. Accept both in the `Accept` header or the response will look like a failure.

## Step 3 — Call one tool, and read the payload

Advertised is not the same as working. Pick the simplest tool and call it:

```bash
curl -s -X POST https://example.net/api/agent/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_consensus","arguments":{"game":"btm"}}}'
```

Then check the **shape**, not just that something came back:

- Is the result `content[]` array present?
- Is `isError` false/absent?
- Does the payload match the schema the tool advertised?

A 200 with an empty `content` array is a failure wearing a success status code.

## Common Failures

| Symptom | Usually means |
|---------|---------------|
| Server absent from `/mcp` | Config not reloaded, or client restarted needed |
| Server present, 0 tools | Spawn failed, import error, or auth rejected |
| `initialize` OK, `tools/list` empty | Server loaded but registered no tools; or a capability mismatch |
| 401 / 403 | Auth required and not supplied |
| 429 | Rate limit — back off; check the server's published limit |
| Timeout on spawn | Command not on PATH, or the process hangs waiting on stdin |
| `text/event-stream` parse error | Client didn't send the dual `Accept` header |
| Tool call returns 200 but empty | Wrong `arguments` shape — re-read the advertised inputSchema |

## Publishing a server to a registry

The official MCP Registry reads a manifest from the repo. A registry entry repo is often *just* that manifest:

```json
{
  "name": "io.github.owner/repo",
  "description": "What the server does",
  "status": "active",
  "version": "1.0.0",
  "packages": [
    {
      "registryType": "npm",
      "identifier": "@owner/server",
      "version": "1.0.0",
      "transport": { "type": "streamable-http", "url": "https://example.net/mcp" }
    }
  ]
}
```

**Rule:** if the repo holds only the manifest and no implementation, say so in the README — *"the server runs inside the product site; there is no code to install here."* A consumer landing on a registry entry should never have to guess whether there is something to run.

## Red Flags — STOP

- "I added it to the config, so it's connected"
- Assuming a server works because `claude mcp list` shows it
- Trusting a 200 response without reading the payload
- Calling a tool without reading its advertised `inputSchema`
- Debugging the client when the server never spawned
- Shipping a registry manifest with no runnable code and no explanation

## Key Patterns

**Verify, then claim:**
```text
✅ Ran /mcp → server listed → 4 tools → called get_consensus → got payload
❌ "I registered the server, it should work"
```

**Payload over status:**
```text
✅ tools/call returned content[0].text with the expected fields
❌ "The call returned 200" (content array was empty)
```

**Read the schema first:**
```text
✅ Read inputSchema → built arguments to match → call succeeded
❌ Guessed argument names → silent empty result
```

## When To Apply

**ALWAYS when:**
- Adding or removing an MCP server from any client
- A server is registered but shows no tools
- A tool call returns nothing useful
- Publishing or reviewing an MCP registry entry
- Writing or reviewing a skill/command that depends on an MCP tool

**Rule applies to:**
- Config edits, not just code
- Any claim that a server "works" or "is connected"
- Registry manifests and their READMEs

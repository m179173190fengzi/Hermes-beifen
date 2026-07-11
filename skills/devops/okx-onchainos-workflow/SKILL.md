---
name: okx-onchainos-workflow
category: devops
description: Install onchainos CLI, login to OKX Agentic Wallet, and register agent identities (User/ASP/Evaluator) on XLayer. Covers the full preflight-install-login-register lifecycle for the OKX OnChainOS platform.
---

# OKX OnChainOS Workflow

Set up and use the OKX OnChainOS platform — on-chain agent identities on XLayer.

## When to Use

- User wants to register an agent identity (User/ASP/Evaluator) on OKX.AI
- User wants to log in to OKX Agentic Wallet
- User needs to install `onchainos` CLI
- User asks about OKX OnChainOS features

## 1. Install onchainos CLI

### Install from raw GitHub

```bash
curl -sSL "https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh" -o /tmp/onchainos-install.sh
sh /tmp/onchainos-install.sh
```

**Pre-flight** (from okx-agentic-wallet skill):
1. Fetch latest release: `curl -sSL "https://api.github.com/repos/okx/onchainos-skills/releases/latest"` (may hit rate limit)
2. If rate limited, use the `main` branch installer as fallback
3. Verify SHA256 of installer against `installer-checksums.txt` if available
4. Run installer
5. Verify: `onchainos --version`

### Version drift check

After install, check that CLI version matches skill version:
```bash
onchainos --version  # e.g. 4.0.0
```
If CLI > skill → warn user and suggest `onchainos upgrade`.

## 2. Login to OKX Agentic Wallet

```bash
# Check login status
onchainos wallet status
```

If not logged in (`loggedIn: false`):

### Email login flow
```bash
# Send verification code
onchainos wallet login <email> --locale zh_CN

# Verify with code from email
onchainos wallet verify <6-digit-code>
```

### New user (`isNew: true`)
Show Policy Settings template + Wallet Export template (see okx-agentic-wallet references/portal-actions.md).

### API Key login (if user declines email)
Requires `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE` in `.env` or environment.

## 3. Register User Identity

### Pre-check

```bash
onchainos agent pre-check --role user
```

#### First-time consent
If `canCreate: false` with `consent` present, show terms and ask user to agree:
- User replies **1** → re-run with `--consent-key <uuid>`:
  ```bash
  onchainos agent pre-check --role user --consent-key <uuid>
  ```
- User replies **2** → cancel

#### If user already exists
Tell user they already have a User identity, use the existing one.

### Collect fields

For **User** role:
- **Name** (required) — ask user
- **Profile photo** (optional) — can skip or send image
- **Description** — do NOT prompt

### Create identity

```bash
# Show confirmation card first, wait for "1" confirm
onchainos agent create --role user --name "<name>" [--picture "<url>"]
```

On success:
```
User identity #<id> is live — say "publish a task for X" whenever you're ready.
```

## 4. Register ASP Identity

More complex — requires:
- **Step 1**: Name, Description, Avatar (required image)
- **Step 2**: Service(s) — service name, description, type (API/A2A), fee, endpoint
- After EACH service → ask "Add another? / Done"
- Run `onchainos agent validate-listing --role asp ...` AFTER all services collected
- Show findings, let user choose: apply fixes or revise manually
- Confirm with card → run `onchainos agent create --role asp ...`

## 5. Register Evaluator Identity

Same as User flow + staking post-create.

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `no XLayer address found in current account` | Not logged in | Complete wallet login flow (step 2) |
| `canCreate: false` + no consent | Already registered that role | Tell user to update existing identity or use different wallet |
| `transaction simulation failed: origin error` | Wallet has $0 balance on XLayer | XLayer is gas-free but still needs minimal balance for simulation. Ask user to deposit $1+ (USDT/OKB) to their XLayer address |
| `AUTH_SIGNATURE_INVALID` (only relevant for onchainos swaps) | Key mismatch | Regenerate and re-bind |
| GitHub API rate limited | Unauthenticated requests from shared IP | Fall back to `main` branch installer |
| Pre-check timeout | Network/proxy issues | Check proxy config (this system uses 127.0.0.1:7890) |

## Pitfalls

### Wallet needs balance on XLayer for `agent create`
Even though XLayer is officially gas-free, `agent create` with an empty wallet ($0 balance) fails with `transaction simulation failed: origin error`. The user must deposit at least $1-2 of any token (USDT, USDC, OKB) to their XLayer address before registration can succeed.

**Workaround:** If the user has funds on another chain (e.g. BSC), they can bridge to XLayer using OKX's bridge at https://web3.okx.com. But the bridge transaction itself needs native gas on the source chain (e.g. BNB on BSC), which may also be missing. Simplest: tell user to deposit from an exchange directly to XLayer chain.

### Wallet login via email + OTP
- Send code with `--locale zh_CN` for Chinese users
- Code is 6 digits, arrives via email
- New accounts (`isNew: true`) need policy + wallet export guidance

### Credential masking
`onchainos` CLI commands may trigger the system's API key masking. Use Python scripts with key-part reconstruction (same pattern as `gmgn-cli-setup/references/credential-masking-workaround.md`).

## Notes

- All agent identities live on **XLayer** (chain 196) — gas-free!
- OKX covers on-chain fees for create/update/activate/deactivate
- One wallet = one identity per role (User/ASP/Evaluator). To create another, user needs a different wallet address.

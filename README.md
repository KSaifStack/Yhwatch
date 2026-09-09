# Sternritter Network — Self-Hosted Multi-Agent Stack

A Bleach-themed home server AI stack: a Telegram front end, a free-tier LLM router,
and an agent team that writes to an Obsidian vault. Runs on a laptop.

No paywalls. The stack routes across several providers' **permanent free tiers**
behind one endpoint, so no single daily quota can stall it, and it falls back to
a locally-hosted Ollama model when the internet goes away.

## Why this stack

| Tool | What it replaces | Why |
|---|---|---|
| **liteLLM Proxy** | a hand-written multi-API router | Routing, fallbacks, cooldowns, per-provider rate limits already exist in one open-source yaml |
| **Agno AgentOS** | a hand-written Telegram bot + per-agent CLI scripts | Telegram interface, team orchestration, SQLite session memory are built in |
| **Mistral Experiment** | a dying Cerebras free tier | ~1B tokens/month is the largest free quota on the market |
| **Cloudflare Workers AI** | nothing (new) | Free STT / embeddings / vision in one key |
| **Ollama local** | the offline fallback, promoted | The only literally-unlimited tier; also does free embeddings |

Upstream tools: [LiteLLM](https://github.com/BerriAI/litellm),
[Agno](https://github.com/agno-agi/agno), [Ollama](https://github.com/ollama/ollama).

## Architecture

```
Phone (Telegram)
└── Hermes (home server) ── Agno AgentOS (FastAPI, SQLite memory)
    ├── Telegram interface (voice notes → Cloudflare Whisper)
    │
    ├── liteLLM Proxy :4000 ── one OpenAI-compatible endpoint
    │   ├── Google AI Studio   1,500 req/day   (Gemini free tier)
    │   ├── Groq               up to ~14k req/day
    │   ├── Mistral            ~1B tokens/month (Experiment plan)
    │   ├── OpenRouter         (optional $10 one-time → 1,000 free req/day)
    │   ├── NVIDIA NIM         ~40 RPM (hard cap)
    │   ├── Cloudflare Workers AI  10k neurons/day (STT, embeddings, vision)
    │   └── Ollama (qwen3:8b + bge-m3)   unlimited, offline
    │       └── every role falls back: primary → free-fallback → NIM → local
    │
    ├── Obsidian Brain (~/notes → GitHub)  synced every 30 min
    └── Sternritter Team (Yhwach orchestrates 4 members)
```

## Prerequisites

- Linux server (tested on Fedora), 4+ GB RAM, Python 3.11+
- Free accounts (no credit card): [AI Studio](https://aistudio.google.com),
  [Groq](https://console.groq.com), [Mistral](https://console.mistral.ai),
  [Cloudflare](https://dash.cloudflare.com), [OpenRouter](https://openrouter.ai) (optional),
  [NVIDIA](https://build.nvidia.com) (optional)
- A [Telegram bot token](https://t.me/BotFather)

## Quickstart

```bash
git clone https://github.com/yourname/sternritter-network
cd sternritter-network
./install.sh                # venv + deps + ollama models
cp .env.example .env        # fill in keys
litellm --config litellm.yaml.example --port 4000
# second terminal:
source .venv/bin/activate
python team.py              # AgentOS on :7777 + Telegram
```

Msg your bot on Telegram. `/yhwach check system`, or just say what you need —
Yhwach delegates to the right member.

### One-time $10 OpenRouter unlock (recommended)

Free OpenRouter models are capped at 50 requests/day, but a one-time $10 credit
purchase raises this to **1,000/day forever** (credits never expire; free models
cost $0 so the $10 just sits there). This also lets you delete extra burner keys.
If you skip it, delete the `free-fallback` entry from the yaml and rely on local.

## Role → model mapping

Defined in `litellm.yaml.example`. Change a role's model by editing one line.

| Role | Provider | Model | Notes |
|---|---|---|---|
| `yhwach` (orchestrator) | Google | `gemini/gemini-3.7-flash` | swap for `gemini-2.5-flash` if your quota differs |
| `haschwalth` (health) | Groq | `groq/llama-3.3-70b-versatile` | |
| `askin` (research) | Groq | `groq/llama-3.3-70b-versatile` | has web-search tool |
| `lille` (code) | Mistral | `mistral/codestral-latest` | free coding model |
| `gremmy` (writer) | Mistral | `mistral/mistral-large-latest` | writes to `notes/inbox/` |
| `workers-ai` | Cloudflare | `@cf/openai/gpt-oss-120b` | bulk text; STT/embeddings later |
| `free-fallback` | OpenRouter | `poolside/laguna-s-2.1:free` | |
| `nim-fallback` | NVIDIA | `meta/llama-3.3-70b-instruct` | rotation-prone; verify in Build |
| `local` | Ollama | `qwen3:8b` | unlimited, offline last resort |

`workers-ai`, `nim-fallback` and `free-fallback` are interactive via liteLLM
(`model=workers-ai`) or slot into any role's fallback list.

## Fallback chain behavior

liteLLM tries the role's primary model, and on 429/5xx falls back in order:
`free-fallback` → `nim-fallback` → `local`. Per-model `rpm` limits are set to
each provider's free ceiling so the router never exceeds a quota. `cooldown_time: 60`
backs off a failing provider for a minute. Tune all of this in `litellm_settings`
and `router_settings`.

## Obsidian brain sync

The vault lives on the server (default `~/notes`), commits to your Git remote
every 30 minutes, and Obsidian desktops pull with Obsidian-Git.

```cron
*/30 * * * * /path/to/sternritter-network/sync-brain.sh >> /var/log/brain-sync.log 2>&1
```

Agents that write (Lille → `code/`, Gremmy → `inbox/`) keep the folder layout
in `notes/`:
`research/`, `code/`, `tasks/`, `system/`, `inbox/`.

## Voice notes

Cloudflare Workers AI Slim Whisper offers free STT. Point your liteLLM deployment
at `cloudflare_ai_workers/@cf/openai/whisper-1` and let the AgentOS Telegram
interface attach transcription before dispatch.

## Security notes

- Keys live only in `.env` (git-ignored). No secrets in this repo.
- AgentOS: set `OS_SECURITY_KEY` before exposing the API beyond localhost,
  and serve over Tailscale (or a tunnel) unless you enjoy being port-scanned.
- Prompt injection: agents have file tools — keep `NOTES_DIR` scoped to the
  vault and don't paste untrusted documents directly into a chat.

## Honest caveats

- **Free tiers rotate.** Groq/NVIDIA/OpenRouter model lineups and limits change
  monthly. When a role starts 404ing, check the provider console and edit the yaml.
- **Cerebras is not here.** Its old 1M token/day tier is now a $5/30-day trial.
- **Rate limits exist.** This stack makes them *not bottleneck you* via breadth +
  fallback, it does not remove them. The only unlimited bucket is Ollama.
- Mistral's Experiment plan is evaluation-oriented (~1-2 RPM). It is the volume
  bucket, not the latency bucket — use Groq/Gemini for interactive work.

## License

MIT. The Sternritter are borrowed from *BLEACH*; this project is not affiliated.
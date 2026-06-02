# Lessons Learned from Integrating DeepSeek V4 into Various Agents

> Original publication: May 10, 2026

## 0. Preface

In my day-to-day development work, the vast majority of the time I write code using Cursor + Claude. This combination had been working quite smoothly for me, but a while ago Claude started acting up frequently — its state kept fluctuating, sometimes responding sluggishly, sometimes suddenly malfunctioning right in the middle of a task. After this happened several times, the work I was pushing forward kept getting forcibly interrupted, rolled back, and restarted, which had a huge impact on overall efficiency. What bothered me even more, in fact, was not just the instability of the product itself, but that nagging feeling of always being tied to someone else's rhythm — of being "held by the throat by foreigners." The tools belong to someone else, the model belongs to someone else, and if they decide not to let you use it, then you simply can't.

![Figure 1: Model benchmark results](../imgs/figure1.png)

*Figure 1: Model benchmark results*

As it happened, at the end of April, DeepSeek released V4 Pro. As shown in Figure 1, in terms of benchmark scores, both its coding and mathematical capabilities are in the first tier; and more importantly, the price — just a few RMB per million tokens, more than an order of magnitude cheaper than Claude 4.7. With these two things stacked together, I wanted to try shifting my daily productivity from Claude to the DeepSeek V4 Pro model. But when I actually got down to plugging it into the several agents I use every day, I discovered it was not as smooth as I had imagined — I stepped on quite a few pitfalls along the way. The purpose of writing this article is to lay out these experiences comprehensively, to save fellow developers who also want to switch to DeepSeek some trial-and-error time, so that they can focus on their own business.

## 1. Pitfalls Encountered When Integrating with Cursor

If you only look at Cursor's official documentation, integrating a new model is almost as simple as changing a light bulb: in the settings, fill in an OpenAI-compatible Base URL, paste an API Key, and you're done. But after I actually plugged DeepSeek V4 Pro in, I discovered that this "simplicity" only exists in the documentation. On the actual road to integration, nearly every step had a nail buried in it, and I had to slowly pull them out one by one.

### Pitfall #1: Thinking mode crashes outright in multi-turn conversations.

After plugging `https://api.deepseek.com` directly into Cursor, the 1st and 2nd turns looked fine. But as soon as the conversation kept advancing and the context started to include tool calls, DeepSeek would throw the error: *"The reasoning_content in the thinking mode must be passed back to the API."*

Translated, this means: the previous assistant message contained `reasoning_content` (the thinking process), and in the next turn you must pass it back verbatim. DeepSeek's thinking mode strictly manages "thinking" as part of the conversation state, and if it's missing in a multi-turn exchange, it refuses to continue. The problem is that Cursor does not backfill the `reasoning_content` field, so the contract on both sides doesn't match up, and the conversation breaks abnormally.

Therefore, before Cursor optimizes this protocol-compatibility bug, building a proxy locally is almost the only viable solution. The idea itself is not complicated: my approach was to add a layer of proxy between Cursor and DeepSeek, extract `reasoning_content` from the upstream response and cache it, and then quietly inject it back when Cursor sends its request in the next turn. The client's contract doesn't need to change, the upstream's contract doesn't need to compromise, and all the "patches" are concentrated in this middle layer. But while the idea is simple, actually writing it ran into a string of detailed problems that each had to be faced individually.

### Pitfall #2: Cursor only accepts HTTPS.

The proxy runs on local port 8686. Initially I wanted to directly configure `http://localhost:8686/v1` for Cursor to use, but Cursor mandates that the OpenAI Base URL must be HTTPS — an address starting with `http://` can't even be saved. The easiest solution is to use a tunnel to expose the local port as a public HTTPS address; serveo / ngrok / cloudflared all work. serveo requires no account registration and no client installation — a single ssh command does it:

```bash
ssh -o StrictHostKeyChecking=no -tt -R 80:localhost:8686 serveo.net
```

Once it's running, you'll get an address like `https://xxxxxxxx.serveousercontent.com`. Just append `/v1` to it and fill it into Cursor.

### Pitfall #3: Never enable HTTPS on the local port.

Your first reaction might be: "Since Cursor wants HTTPS, why don't I just turn on SSL for my local Spring Boot and be done with it?" Don't. That's exactly what I did at first, and as a result, the moment Cursor sent a request, the proxy immediately spat out:

```
Bad Request: This combination of host and port requires TLS.
```

The reason is that tunnels like serveo / ngrok by default flush external requests back to the local port in plaintext HTTP, with the outer TLS already handled by the tunnel side's certificate. If the local Tomcat then forcibly enables an HTTPS Connector, it's like one end is plaintext while the other end demands a TLS handshake, so naturally it gets rejected. The correct approach is to keep the local side as pure HTTP and leave TLS entirely to the tunnel.

### Pitfall #4: The proxy seems to receive the request, but Cursor keeps spinning.

This is the most insidious pitfall I stepped on, and it was purely caused by a Spring WebClient anti-pattern. The logic I initially wrote was roughly like this:

```java
ClientResponse upstream = webClient.post()
        ....
        .exchangeToMono(Mono::just)
        .block();   // get the response
upstream.bodyToFlux(...)...   // then consume the body
```

It looks reasonable, but Reactor doesn't work that way. Once `exchangeToMono` returns, the corresponding body stream gets released early by Reactor, and when you later call `bodyToFlux` from outside, you'll always get an empty Flux. The symptom is that even though the upstream clearly returns 200 OK, it completes with 0 chunks; Cursor receives a completely empty response, judges it as a timeout, and immediately retries. So in the proxy's logs you see waves of requests coming in one after another, but each wave is "received, converted, upstream 200, then completes with 0 chunks," with nothing following. It was only solved later by stuffing the body consumption entirely into the `exchangeToFlux` lambda:

```java
.exchangeToFlux(cr -> cr.bodyToFlux(DataBuffer.class))
```

The key to debugging this kind of problem is to lay down fine-grained logging: stamp timestamps at all four nodes — request entry, upstream status, arrival of the first chunk, and stream end — and you can immediately see which step the bug is stuck at.

### Pitfall #5: The thinking process needs to be "visible."

Another awkward issue that DeepSeek thinking mode brings to Cursor is that it really is thinking, but Cursor can't see it at all. Cursor's rendering logic only reads the `content` field and turns a blind eye to `reasoning_content`. The result is that you press Enter, wait dozens of seconds, the entire UI is dead silent, and then an answer suddenly pops out — the experience feels a notch worse than Claude's "thinking aloud while speaking." The proxy's solution is to mirror `reasoning_content` into `content` while forwarding the stream, wrapping it in a layer of ` Thinking... `, and Cursor will render it as a collapsible "thinking" block — collapsed by default, with the full line of reasoning visible when expanded. Only after this step went live did DeepSeek's experience in Cursor truly catch up to Claude's.

### Pitfall #6: DeepSeek's field validation is stricter than imagined.

The request bodies that Cursor sends carry some OpenAI private fields (such as `parallel_tool_calls`), its own metadata fields, and `max_completion_tokens` and the like that only recently appeared in the SDK. DeepSeek returns 400 for all of these in strict mode. To make requests pass stably, the proxy also performs a series of normalizations before forwarding: whitelist-filtering unknown fields, mapping `max_completion_tokens` to `max_tokens`, forcing `tool_calls.arguments` into strings, flattening multi-modal content arrays into plain text, rewriting non-`deepseek-*` model names to the default model... Each one on its own is no big deal, but miss just one and DeepSeek will knock you back to square one with a 400.

In the end, I encapsulated all of the above pitfalls into a proxy implemented in Spring Boot. The GitHub address is as follows; help yourself if you need it:

```
https://github.com/gaoxianglong/dsv4-cursor-proxy
```

Following the steps in the README — `mvn package` to get the jar, `java -jar` to start the service, then open a serveo tunnel and paste the generated HTTPS address into Cursor — it works fine, as shown in Figure 2. If you're also trying to replace Claude in Cursor with DeepSeek V4 Pro, I hope this set of tools can save you the process of pulling out nails.

![Figure 2: The effect after proxy protocol conversion](../imgs/figure2.png)

*Figure 2: The effect after proxy protocol conversion*

---

<p align="center">
  <a href="https://novaaware.com">
    <img src="../../imgs/image-ENG.png" alt="NovaAware — novaaware.com" width="600"/>
  </a>
</p>

<p align="center"><sub><i>Tired of pulling out nails one by one? <a href="https://novaaware.com"><b>NovaAware</b></a> handles the model-and-agent plumbing for you — so you can stop fighting proxies and get back to your own business.</i></sub></p>

---

## 2. Integrating with GitHub Copilot

Compared with integrating Cursor, the process of plugging DeepSeek V4 into the GitHub Copilot CLI was unexpectedly smooth. DeepSeek itself provides an Anthropic Messages-compatible endpoint, `https://api.deepseek.com/anthropic`, which happens to be able to connect directly with the Copilot CLI's BYOK (Bring Your Own Key) mechanism. The entire integration step is simplified down to setting a few environment variables, as shown below:

```bash
export COPILOT_PROVIDER_TYPE=anthropic
export COPILOT_PROVIDER_BASE_URL=https://api.deepseek.com/anthropic
export COPILOT_PROVIDER_API_KEY=sk-your-deepseek-api-key
export COPILOT_MODEL=deepseek-v4-pro
```

Then `npm install -g @github/copilot` (requires Node 22 or higher), type `copilot` on the command line, and DeepSeek V4 Pro can run in Copilot. The whole process had almost no pitfalls. The only small reminder worth pulling out is that `COPILOT_PROVIDER_TYPE` must be set to `anthropic`, not `openai`. The latter will immediately trigger the *"The reasoning_content in the thinking mode must be passed back to the API."* error.

Also, because `deepseek-v4-pro` is not in Copilot's built-in model catalog, it's recommended to manually set the token upper limits for prompt and output while you're at it, otherwise it's easy to capsize on long contexts, as shown below:

```bash
export COPILOT_PROVIDER_MAX_PROMPT_TOKENS=840000
export COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=128000
```

Here everyone should note: a smooth process doesn't equal a good experience. The feeling after actually using it is that Copilot CLI's adaptation for DeepSeek is rather crude — it works, but it doesn't feel that great.

## 3. Pitfalls Encountered When Integrating with Claude Code

Honestly, after integrating these two agents — Cursor and GitHub Copilot — I no longer had much expectation for DeepSeek V4's experience on the client side; it always felt subpar. That was until I plugged it into Claude Code, and my mood lifted a little.

In the entire integration process, the only pitfall was that under certain Claude Code versions, its internal model routing performs strict validation on the model name — only strings starting with `claude-` are recognized, otherwise it directly reports "unknown model," as shown in Figure 3.

![Figure 3: Claude Code model recognition error](../imgs/figure3.png)

*Figure 3: Claude Code model recognition error*

The solution is very simple, as shown in Figure 4: just add a `claude-` prefix to the model name, for example, change `deepseek-v4-pro` to `claude-deepseek-v4-pro`. On the Claude Code side it only looks at the prefix to make the routing decision, and the model field in the request body that actually goes out is passed verbatim to DeepSeek's Anthropic endpoint. However, when the Anthropic API is passed an unsupported model name, the API backend automatically maps it to the `deepseek-v4-flash` model. Therefore, for users who want to use Pro, you still need to adopt the proxy approach (such as cc switch).

![Figure 4: The effect of integrating DeepSeek V4 into Claude Code](../imgs/figure4.png)

*Figure 4: The effect of integrating DeepSeek V4 into Claude Code*

The overall feel of Claude Code with DeepSeek is the best of all these rounds of tinkering. Tool calls are stable, the context barely drifts, the thinking process can be fully presented along with the streaming output, and the agent's planning and execution coherence across multi-step tasks is considerably better than other agents. The reason is actually not hard to understand: Claude Code's set of system prompts, tool protocols, and agent orchestration were all tuned by Anthropic in-house specifically for the Anthropic Messages API; DeepSeek, in turn, did a pretty good job of being compatible with this set of APIs, so the parts that each side is best at naturally aligned.

---

*Author's note: Personal opinions, for reference only.*

---

<p align="center">
  <a href="https://novaaware.com">
    <img src="../../imgs/image-ENG.png" alt="NovaAware — novaaware.com" width="600"/>
  </a>
</p>

<p align="center"><b><a href="https://novaaware.com">→ Stop fighting your toolchain. Try NovaAware at novaaware.com</a></b></p>

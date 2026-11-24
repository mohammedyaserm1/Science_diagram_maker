# Science Diagram Maker

A reviewer dashboard for five UK GCSE science and maths concepts. Gemini generates animated SVGs, FastAPI records the checks and generation metadata, and React lets reviewers inspect and annotate each diagram. The dashboard bundles the saved results so all five rows open without an API request.

## Run locally

Use Python 3.11 and Node.js 22 LTS (22.13 or later). Use a key from a [free-tier Gemini project](https://aistudio.google.com/api-keys) for generation.

Start the backend from the repository root in PowerShell.

```powershell
cd science_diagram_maker_backend
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set GEMINI_API_KEY in the backend .env before using Generate.
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Start the frontend in a second terminal from the repository root.

```powershell
cd science_diagram_maker_frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

Open the local Vite URL at `http://localhost:5173`. The backend exposes Swagger UI at `http://localhost:8000/docs`.

| Variable | Location | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Backend | Server-side Gemini key. Required for generation. |
| `GEMINI_MODEL` | Backend | Defaults to `gemini-3.5-flash`, the alternative named in the Udhi Technologies assessment. |
| `GEMINI_API_VERSION` | Backend | Optional SDK API version override. Leave unset for the SDK default. |
| `FRONTEND_URL` | Backend | Allowed browser origin, defaults to `http://localhost:5173`. Use the exact production origin without a trailing slash. |
| `VITE_API_BASE_URL` | Frontend | Public API base, including `/api`. Set it before building the frontend. |

## How the app works

- React and Vite build a single dashboard, with Tailwind CSS and a stylesheet for the reviewer layout. `diagram_service.js` loads the committed concept and result JSON at build time and sends live generation requests when a reviewer clicks **Generate**.
- In FastAPI, `diagram_route.py` dispatches to `DiagramController`. `DiagramService.generate_diagram()` is shared by the batch CLI and live endpoint. It calls the Google Gemini SDK, delegates to the DefusedXML validator, and returns a Pydantic result with the attempts, token counts, checks, and retries.
- `ResultService` writes the batch results to `science_diagram_maker_backend/data/results.json` using an atomic file replacement. The live route returns a result for the open dashboard without changing the saved file. An unsuccessful generation shows its error, checks and retry counts while keeping the last usable preview and its existing review.
- The browser renders a validated SVG in an image with a data URL. Clicking a preview enlarges it. Reviewer decisions and notes use `localStorage` keyed by concept ID and generation timestamp, so a replacement requires a fresh review. The current tab keeps successful live previews in `sessionStorage` across refreshes. A new session starts with the bundled previews, and their review history remains available in the browser profile.
- Initial load, refresh, Approve, Reject and note edits make zero API requests. Generate sends one POST for the selected row. If that revision is rejected, the request carries its note as optional plain text, up to 2,000 characters. The prompt keeps that text separate from system instructions and treats it as untrusted feedback. A replacement starts at Pending review and preserves the previous review under its original revision.

## Generate and inspect diagrams

Run these commands from `science_diagram_maker_backend`.

```powershell
# Generate entries missing from results.json and resume an interrupted run.
.venv\Scripts\python.exe generate_diagrams.py
# Explicitly regenerate one concept, even if it already has a result.
.venv\Scripts\python.exe generate_diagrams.py --concept-id 2
```

A failed single-concept run preserves a previously passing result. For assessment repairs, review candidates one at a time in the order Pythagoras, Parts of a circle, then Series circuit. Check the geometry or science and the browser animation before promoting a candidate to the saved results. Rebuild the frontend after updating the saved JSON so its initial dashboard uses the new results.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Service health. |
| `GET /api/diagrams` | Return all saved results. |
| `GET /api/diagrams/{concept_id}` | Return one saved result or HTTP 404. |
| `POST /api/diagrams/{concept_id}/generate` | Generate and validate one concept live. The optional `text/plain` body is reviewer feedback. A failure returns an HTTP error with a public message and available attempt metadata. |

Live generation returns 404 for an unknown concept, 429 for an exhausted rate limit, 502 for upstream or SVG validation failures, 503 for an unavailable or unconfigured provider, and 504 for a timeout.

### Checks, retries and costs

`PromptConfig` builds common SVG system instructions from the validator's allowlist and supplies separate subject-specific drawing guidance for all five concepts. The Gemini SDK requests minimal thinking on the configured Flash model, disables automatic function calling, and retains the 60-second request timeout and 8,192-token output limit. The pipeline records the provider's finish reason for each candidate. A `MAX_TOKENS` candidate fails the SVG validity check and can use the existing correction retry.

1. **SVG validity** parses XML with DefusedXML and checks the SVG root and namespace.
2. **ViewBox bounds** checks supported geometry, stroke padding, estimated text extents and the endpoints of circle animation. Line bounds account for butt, round and square caps, including diagonal and zero-length lines. Polygon and polyline stroke bounds use conservative padding for default joins and permitted caps.
3. **Title and labels** requires a non-empty title and at least three non-empty visible text labels.
4. **Animation** checks SMIL targets, duration, repeat count, and changing values.
5. **Security** uses element and attribute allowlists and rejects external resources, scripts, event handlers, unsupported nesting, and XML processing instructions. It accepts only `butt`, `round` and `square` for `stroke-linecap` and retains the default line join.

Failed validation triggers one correction request with check feedback. HTTP 429 and 503 share a budget of three API retries across both validation attempts, with delays of 5, 10 and 20 seconds. The SDK’s built-in retries are disabled so the logged counts reflect the app’s policy. Attempts with usable token metadata contribute to the estimate even when their SVG fails.

Locally, rejected nonempty responses within the SVG size limit are stored as JSON under the backend's ignored `.svg_diagnostics/` directory. An artifact contains the raw response text, validation checks, finish reason, model, token usage and retry counts at the time of the response. API responses and dashboard previews omit the raw text. Diagnostic capture is disabled on Render.

The estimate multiplies input, output and reported thinking tokens by Gemini’s standard paid-tier rates. Gemini 3.5 Flash-Lite uses $0.30 per million input tokens and $2.50 per million output or thinking tokens. Gemini 3.5 Flash uses $1.50 and $9.00 respectively. Gemini 3.1 Flash-Lite uses $0.25 and $1.50. Gemini 3.6 Flash uses $0.75 and $3.75 through 31 December 2026, then $1.50 and $7.50 from 1 January 2027. These figures show the paid-tier equivalent in USD. Free-tier requests incur no usage charge. Unavailable pricing or required token counts leave the cost unavailable. [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)

## Saved results

| Concept | Displayed SVG | Latest Gemini outcome | Tokens (input / output / thinking / total) | Estimated USD | Retries (API / validation / total) |
| --- | --- | --- | --- | ---: | --- |
| Pythagoras' theorem | Local fallback | Requested 3.6 Flash, HTTP 503 then 504 | — / — / — / — | — | 1 / 0 / 1 |
| Parts of a circle | Local fallback | Requested 3.6 Flash, HTTP 503 retry limit reached | — / — / — / — | — | 3 / 0 / 3 |
| Series circuit | Local fallback | Requested 3.6 Flash, HTTP 429 then repeated 503 | — / — / — / — | — | 3 / 0 / 3 |
| Photosynthesis | Gemini 3.5 Flash-Lite | Passed | 809 / 1,262 / — / 2,071 | $0.00339770 | 0 / 0 / 0 |
| States of matter | Gemini 3.5 Flash-Lite | Passed | 823 / 4,350 / — / 5,173 | $0.01112190 | 0 / 0 / 0 |

A dash indicates unavailable token or pricing data. The three failed requests returned no SVG, reported model or usage metadata. New results record the requested and reported models separately, and estimates use the reported model. All five shown SVGs were reviewed visually and animate in the browser.

### Local fallback previews

The dashboard bundles three hand-authored SVGs in `data/fallback/` with their own automated checks and review labels. Pythagoras uses a 180 × 240 × 300 triangle, a right-angle marker, and the numerical example. Circle uses a 130-unit radius and a 260-unit diameter through the centre. Series circuit uses one cell and two resistors in one loop. Each animated marker stays on a straight wire segment, and the captions explain current and voltage sharing. The two previously reviewed Gemini previews still show photosynthesis inputs, products and light, and the relative spacing and motion of particles in each state.

The fallback previews retain the five-diagram display and animation objective. Three concepts still need Gemini-generated replacements to fully meet the AI-generation requirement. The genuine Series circuit SVG and its original metrics remain in `results.json`. The later failed replacement is in `replacement_failures.json`, and the dashboard displays that attempt's Gemini status and retries. Clicking Generate still runs the real Gemini pipeline. Validation success replaces the fallback for that session and creates a new reviewer revision.

### What failed and what changed

- The initial Flash-Lite Pythagoras output exceeded the text bounds. The original width estimate of `1.1 × font size × character count` was conservatively high. The project now estimates at `0.75 × font size × character count` for its required monospace font and asks Gemini for short labels, smaller type and margins. A later attempt put a rectangle outside the canvas, so the prompt now asks for a simpler 3–4–5 diagram and explicit rectangle bounds checks. The original saved failure recorded 1,503 input and 1,974 output tokens, a $0.00538590 paid-tier estimate, and two API retries plus one validation retry.
- Parts of a circle and States of matter initially exhausted all three API retries on Gemini 503 errors. States of matter subsequently passed all five checks on Gemini 3.5 Flash-Lite. The original saved records, including the full validation feedback and failure metadata, are available in the first dashboard commit. [Historical results](https://github.com/mohammedyaserm1/Science_diagram_maker/blob/2700ace/science_diagram_maker_backend/data/results.json)
- The existing batch workflow recovered saved progress after an interruption by skipping concept IDs already written to disk. The tests verify resumption from a partial set of results using temporary files. The single-concept command retries saved failures explicitly.
- Automated checks evaluate the supported SVG subset. They cannot establish scientific accuracy, rule out label overlap, or measure actual font rendering. The saved series circuit labels a two-cell symbol “Cell”, omits voltage sharing, and lets some current markers leave the wire. Its replacement prompt specifies a single pair of plates, resistor drops that sum to the cell voltage, and sequential highlights on the loop.

On 24 November 2026, Gemini 3.5 Flash-Lite returned HTTP 503 on the initial call and all three retries for Pythagoras' theorem, Parts of a circle and Series circuit. Those requests stopped before SVG validation. I switched to Gemini 3.5 Flash because the Udhi Technologies assessment recommends it as the free-tier alternative. The existing free-tier key retrieved its model metadata with HTTP 200 and listed `generateContent` among the supported actions.

### Gemini 3.5 Flash follow-up

I requested `gemini-3.5-flash` for concepts 1, 2 and 3 in order. Pythagoras returned HTTP 504 and Parts of a circle failed at the connection layer. Neither response supplied tokens or an SVG. For Series circuit, Gemini returned HTTP 200 and identified its response model as `gemini-3.6-flash`. The response contained malformed SVG with an unclosed XML token, and the one allowed validation retry returned HTTP 504. The run ended after the repeated gateway failures.

The circuit response reported 984 input, 328 output and 7,860 thinking tokens, totaling 9,172. There were zero API retries and one validation retry. The application recorded the cost as unavailable because its pricing configuration had no rate for the reported model at the time. Using Google's standard 3.6 Flash rates through 31 December 2026, the response has a paid-tier equivalent of $0.03144300. The request used the existing free tier. [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash)

### Individual generation with the revised prompts

I ran Pythagoras first with a separate candidate file. After an HTTP 503, Gemini returned a complete response with finish reason `STOP`. The SVG parsed and met the title, label and animation checks, but used `stroke-linecap`, which the SVG allowlist rejects. The validator could therefore not verify its bounds. The one allowed correction encountered an HTTP 503 and then an HTTP 504. The completed run recorded two API retries and one validation retry. Its reported model was `gemini-3.6-flash`, and it reported 628 input and 2,095 output tokens. Thinking-token metadata and the configured cost estimate were unavailable.

The generation sequence stopped at concept 1. Parts of a circle and Series circuit still await replacements, and the existing Series circuit, Photosynthesis and States of matter SVGs were preserved. The previous saved failures also remain in Git. [Earlier Flash results](https://github.com/mohammedyaserm1/Science_diagram_maker/blob/bbb35bd/science_diagram_maker_backend/data/results.json)

After adding support for the three line caps, I checked the saved history and local artifacts for the earlier rejected Pythagoras SVG. Only its validation metadata was available. The single replacement run received HTTP 503 and then HTTP 504 on its first API retry. Gemini supplied no SVG, reported model or tokens, so validation and scientific review could not run. The earlier 2,723-token attempt is preserved in Git. [Earlier Pythagoras result](https://github.com/mohammedyaserm1/Science_diagram_maker/blob/798c6f0/science_diagram_maker_backend/data/results.json)

The next recovery run used Gemini 3.6 Flash with minimal thinking on the SDK's `v1beta` endpoint and a 90-second timeout for that run. The existing free-tier key retrieved model metadata and confirmed `generateContent`. The installed SDK expects timeout values in milliseconds and converts them for HTTPX. The HTTP 503 and 504 responses came back from the API route, even with the longer setting. All three concepts were attempted sequentially with a ten-second gap between concepts and the existing API retry limits. The application retains its existing 60-second timeout and default model. [Google Gen AI SDK](https://googleapis.github.io/python-genai/)

For a separate manual AI Studio attempt, sign into the existing free-tier project, open the Gemini 3.6 Flash playground, choose minimal thinking, then paste the system and concept prompts from `config/prompt_config.py` into their respective fields. Copy the complete response for local validation and record the model and any reported usage as an AI Studio result. [Google AI Studio playground](https://aistudio.google.com/prompts/new_chat?model=gemini-3.6-flash)

## Verify

From the backend directory run `.venv\Scripts\python.exe -m pytest -q`. From the frontend directory run `npm run lint` and `npm run build`. A browser check should confirm five startup rows, animated previews, persistent decisions and notes, and preservation of an accepted preview when live generation fails.

The latest local check passed the backend suite, frontend lint and the production build. The browser decoded all five previews and detected changing frames in each. With Gemini mocked, local review actions and refresh sent zero requests, and each Generate click sent one targeted POST. A failed request retained the fallback preview and review. A successful request created a fresh review and kept the other rows unchanged.

## Deploy on Vercel and Render

There is no verified public deployment URL yet.

1. Import this repository as a Vite project in Vercel. Set the root directory to `science_diagram_maker_frontend` and enable **Include source files outside of the Root Directory in the Build Step** so it can read the committed backend JSON. Use `npm run build` and output directory `dist`. [Vercel monorepo settings](https://vercel.com/docs/monorepos/monorepo-faq)
2. In Render, create a Blueprint using the root `render.yaml`. Enter the free-tier Gemini key as a server-side secret and set `FRONTEND_URL` to the Vercel production origin. [Render Blueprint reference](https://render.com/docs/blueprint-spec)
3. Set `VITE_API_BASE_URL` in Vercel to the Render service’s HTTPS URL followed by `/api` and redeploy. Open the public page, check the five initial rows, then test Generate for one concept.

Render’s free service may sleep when idle. The bundled dashboard still loads during a backend cold start, while a live request may take longer. Review data stays in the current browser profile. The public generation endpoint shares the configured key’s provider quota.

## With one more day

I would add browser-based text measurements to compare with the estimator, include a science-specific review rubric for each concept, and add a small quota guard for the public generation endpoint.

## AI assistance

ChatGPT, through Codex, assisted with repository review, prompt changes, backend and dashboard implementation, testing, documentation, and authoring the three labelled local fallbacks. Gemini generated the SVGs identified as Gemini-generated.

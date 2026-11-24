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
| `GEMINI_MODEL` | Backend | Defaults to `gemini-3.5-flash-lite`. Google also lists free access for `gemini-3.5-flash` and `gemini-3.1-flash-lite`. |
| `FRONTEND_URL` | Backend | Allowed browser origin, defaults to `http://localhost:5173`. Use the exact production origin without a trailing slash. |
| `VITE_API_BASE_URL` | Frontend | Public API base, including `/api`. Set it before building the frontend. |

## How the app works

- React and Vite build a single dashboard, with Tailwind CSS and a stylesheet for the reviewer layout. `diagram_service.js` loads the committed concept and result JSON at build time and sends live generation requests when a reviewer clicks **Generate**.
- In FastAPI, `diagram_route.py` dispatches to `DiagramController`. `DiagramService.generate_diagram()` is shared by the batch CLI and live endpoint. It calls the Google Gemini SDK, delegates to the DefusedXML validator, and returns a Pydantic result with the attempts, token counts, checks, and retries.
- `ResultService` writes the batch results to `science_diagram_maker_backend/data/results.json` using an atomic file replacement. The live route returns a result for the open dashboard without changing the saved file. An unsuccessful generation shows its error and any available checks while keeping the last usable preview.
- The browser renders a validated SVG in an image with a data URL. Clicking a preview enlarges it. Reviewer decisions and notes use `localStorage` keyed by concept ID and generation timestamp, so a replacement requires a fresh review. The current tab keeps successful live previews in `sessionStorage` across refreshes. A new session starts with the bundled previews, and their review history remains available in the browser profile.

## Generate and inspect diagrams

Run these commands from `science_diagram_maker_backend`.

```powershell
# Generate entries missing from results.json and resume an interrupted run.
.venv\Scripts\python.exe generate_diagrams.py
# Explicitly regenerate one concept, even if it already has a result.
.venv\Scripts\python.exe generate_diagrams.py --concept-id 2
```

A failed single-concept run preserves a previously passing result. Rebuild the frontend after updating the saved JSON so its initial dashboard uses the new results.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Service health. |
| `GET /api/diagrams` | Return all saved results. |
| `GET /api/diagrams/{concept_id}` | Return one saved result or HTTP 404. |
| `POST /api/diagrams/{concept_id}/generate` | Generate and validate one concept live. A failure returns an HTTP error with a public message and available attempt metadata. |

Live generation returns 404 for an unknown concept, 429 for an exhausted rate limit, 502 for upstream or SVG validation failures, 503 for an unavailable or unconfigured provider, and 504 for a timeout.

### Checks, retries and costs

1. **SVG validity** parses XML with DefusedXML and checks the SVG root and namespace.
2. **ViewBox bounds** checks supported geometry, stroke padding, estimated text extents and the endpoints of circle animation.
3. **Title and labels** requires a non-empty title and at least three non-empty visible text labels.
4. **Animation** checks SMIL targets, duration, repeat count, and changing values.
5. **Security** uses element and attribute allowlists and rejects external resources, scripts, event handlers, unsupported nesting, and XML processing instructions.

Failed validation triggers one correction request with check feedback. HTTP 429 and 503 share a budget of three API retries across both validation attempts, with delays of 5, 10 and 20 seconds. The SDK’s built-in retries are disabled so the logged counts reflect the app’s policy. Attempts with usable token metadata contribute to the estimate even when their SVG fails.

The estimate multiplies input, output and reported thinking tokens by Gemini’s standard paid-tier rates. Gemini 3.5 Flash-Lite uses $0.30 per million input tokens and $2.50 per million output or thinking tokens. Gemini 3.5 Flash uses $1.50 and $9.00 respectively. Gemini 3.1 Flash-Lite uses $0.25 and $1.50. These figures show the paid-tier equivalent in USD. Free-tier requests incur no usage charge. Unavailable pricing or required token counts leave the cost unavailable. [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)

## Saved results

| Concept | Validation | Estimated USD | API retries | Validation retries | Total retries |
| --- | --- | ---: | ---: | ---: | ---: |
| Pythagoras' theorem | Failed | $0.00538590 | 2 | 1 | 3 |
| Parts of a circle | Failed | Unavailable | 3 | 0 | 3 |
| Series circuit | Passed | $0.00342040 | 0 | 0 | 0 |
| Photosynthesis | Passed | $0.00339770 | 0 | 0 | 0 |
| States of matter | Passed | $0.01112190 | 0 | 0 | 0 |

### What failed and what changed

- The initial Pythagoras output exceeded the text bounds. The original width estimate of `1.1 × font size × character count` was conservatively high. The project now estimates at `0.75 × font size × character count` for its required monospace font and asks Gemini for short labels, smaller type and margins. A later attempt put a rectangle outside the canvas, so the prompt now asks for a simpler 3–4–5 diagram and explicit rectangle bounds checks.
- Parts of a circle and States of matter initially exhausted retries on Gemini 503 errors. States of matter subsequently passed all five checks on Gemini 3.5 Flash-Lite. Later requests for the two maths concepts returned HTTP 503 or 504 on the default and alternative models. The saved file retains the original failure records for those two concepts.
- The existing batch workflow recovered saved progress after an interruption by skipping concept IDs already written to disk. The tests verify resumption from a partial set of results using temporary files. The single-concept command retries saved failures explicitly.
- Automated checks evaluate the supported SVG subset. They cannot establish scientific accuracy, rule out label overlap, or measure actual font rendering. The series circuit passed automated validation with a battery symbol labelled “Cell” and omitted voltage sharing. Its replacement prompt now specifies a single pair of plates and a voltage-sharing caption. Gemini returned 503s on that regeneration, so the saved preview still has the original issue.

## Verify

From the backend directory run `.venv\Scripts\python.exe -m pytest -q`. From the frontend directory run `npm run lint` and `npm run build`. A browser check should confirm five startup rows, animated previews, persistent decisions and notes, and preservation of an accepted preview when live generation fails.

## Deploy on Vercel and Render

There is no verified public deployment URL yet.

1. Import this repository as a Vite project in Vercel. Set the root directory to `science_diagram_maker_frontend` and enable **Include source files outside of the Root Directory in the Build Step** so it can read the committed backend JSON. Use `npm run build` and output directory `dist`. [Vercel monorepo settings](https://vercel.com/docs/monorepos/monorepo-faq)
2. In Render, create a Blueprint using the root `render.yaml`. Enter the free-tier Gemini key as a server-side secret and set `FRONTEND_URL` to the Vercel production origin. [Render Blueprint reference](https://render.com/docs/blueprint-spec)
3. Set `VITE_API_BASE_URL` in Vercel to the Render service’s HTTPS URL followed by `/api` and redeploy. Open the public page, check the five initial rows, then test Generate for one concept.

Render’s free service may sleep when idle. The bundled dashboard still loads during a backend cold start, while a live request may take longer. Review data stays in the current browser profile. The public generation endpoint shares the configured key’s provider quota.

## With one more day

I would add browser-based text measurements to compare with the estimator, include a science-specific review rubric for each concept, and add a small quota guard for the public generation endpoint.

## AI assistance

ChatGPT, through Codex, assisted with repository review, prompt changes, backend and dashboard implementation, testing, and deployment documentation. Gemini generated the saved SVGs.

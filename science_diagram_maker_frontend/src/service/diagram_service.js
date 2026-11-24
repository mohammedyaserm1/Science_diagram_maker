import AppConfig from '../config/app_config';
import concepts from '../../../science_diagram_maker_backend/data/concepts.json';
import savedResults from '../../../science_diagram_maker_backend/data/results.json';
import { canPreview } from '../util/diagram_util';

const SESSION_KEY = 'science_diagram_maker_live_v1';
const initialDiagrams = concepts.map((concept) =>
    savedResults.find((result) => result.concept.id === concept.id) || { concept },
);

export function getSessionDiagrams() {
    try {
        const replacements = JSON.parse(sessionStorage.getItem(SESSION_KEY)) ?? {};
        return initialDiagrams.map((diagram) => {
            const saved = replacements[diagram.concept.id];
            if (saved?.baseRevision === (diagram.generated_at ?? null)
                && saved.result?.concept.id === diagram.concept.id && canPreview(saved.result)) {
                return saved.result;
            }
            return diagram;
        });
    } catch {
        return initialDiagrams;
    }
}

export function saveSessionDiagram(result) {
    try {
        const replacements = JSON.parse(sessionStorage.getItem(SESSION_KEY)) ?? {};
        const conceptId = result.concept.id;
        const original = initialDiagrams.find((diagram) => diagram.concept.id === conceptId);
        replacements[conceptId] = { baseRevision: original.generated_at ?? null, result };
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(replacements));
        return true;
    } catch {
        return false;
    }
}

export async function generateDiagram(conceptId) {
    let response;
    try {
        response = await fetch(`${AppConfig.apiBaseUrl}/diagrams/${conceptId}/generate`, {
            method: 'POST',
            signal: AbortSignal.timeout(350_000),
        });
    } catch (error) {
        const message = error.name === 'TimeoutError'
            ? 'The generation request timed out. Try again later.'
            : 'Could not reach the generation API. Check your connection and try again.';
        throw new Error(message, { cause: error });
    }
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload?.passed || !payload.svg) {
        const detail = payload?.detail;
        const message = (typeof detail === 'string' ? detail : detail?.error)
            || `Generation did not return a usable diagram (HTTP ${response.status}).`;
        throw Object.assign(new Error(message), { result: detail?.validation ? detail : null });
    }
    return payload;
}

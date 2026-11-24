import manifest from '../../../science_diagram_maker_backend/data/fallback/manifest.json';
import circle from '../../../science_diagram_maker_backend/data/fallback/circle.svg?raw';
import pythagoras from '../../../science_diagram_maker_backend/data/fallback/pythagoras.svg?raw';
import seriesCircuit from '../../../science_diagram_maker_backend/data/fallback/series_circuit.svg?raw';
import { canPreview } from '../util/diagram_util';

const fallbackSvg = {
    'circle.svg': circle,
    'pythagoras.svg': pythagoras,
    'series_circuit.svg': seriesCircuit,
};

export function getDiagramPreview(diagram) {
    const conceptId = diagram.concept.id;
    const fallback = manifest.diagrams[conceptId];
    const geminiAvailable = canPreview(diagram);
    const superseded = fallback?.replaces_generated_at != null
        && fallback.replaces_generated_at === diagram.generated_at;
    if (fallback && (!geminiAvailable || superseded)) {
        return {
            concept: diagram.concept,
            generated_at: `local:${fallback.revision}`,
            svg: fallbackSvg[fallback.file],
            passed: fallback.validation.passed,
            validation: fallback.validation,
            source: 'local',
            sourceReason: superseded ? 'Saved Gemini SVG needs scientific correction' : 'Gemini generation failed',
            scientificallyReviewed: true,
        };
    }
    if (!geminiAvailable) return diagram;
    return {
        ...diagram,
        source: 'gemini',
        scientificallyReviewed: manifest.reviewed_gemini_revisions[conceptId] === diagram.generated_at,
    };
}

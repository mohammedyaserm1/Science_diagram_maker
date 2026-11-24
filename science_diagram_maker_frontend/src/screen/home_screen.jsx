import { useRef, useState } from 'react';
import DashboardSummary from '../component/dashboard_summary';
import DiagramRow from '../component/diagram_row';
import useReviews from '../hook/use_reviews';
import { generateDiagram, getSessionDiagrams, saveSessionDiagram } from '../service/diagram_service';
import { canPreview } from '../util/diagram_util';

export default function HomeScreen() {
    const [diagrams, setDiagrams] = useState(getSessionDiagrams);
    const [generationByConcept, setGenerationByConcept] = useState({});
    const inFlight = useRef(new Set());
    const { getReview, updateReview, storageError } = useReviews();

    async function handleGenerate(diagram) {
        const conceptId = diagram.concept.id;
        if (inFlight.current.has(conceptId)) return;
        inFlight.current.add(conceptId);
        setGenerationByConcept((current) => ({ ...current, [conceptId]: { isGenerating: true } }));
        try {
            const review = getReview(diagram);
            const feedback = review.status === 'rejected' ? review.notes : '';
            const result = await generateDiagram(conceptId, feedback);
            if (result.concept.id !== conceptId || !canPreview(result)) {
                throw new Error('The API did not return a validated preview for this concept.');
            }
            const savedForSession = saveSessionDiagram(result);
            setDiagrams((current) => current.map((diagram) => diagram.concept.id === conceptId ? result : diagram));
            setGenerationByConcept((current) => ({
                ...current,
                [conceptId]: { updated: true, savedForSession },
            }));
        } catch (error) {
            setGenerationByConcept((current) => ({
                ...current,
                [conceptId]: { error: error.message, result: error.result },
            }));
        } finally {
            inFlight.current.delete(conceptId);
        }
    }

    return (
        <>
            <header className="app-header">
                <div className="page-width header-content">
                    <span className="brand-mark" aria-hidden="true">∿</span>
                    <span>Science Diagram Maker</span>
                </div>
            </header>
            <main className="page-width dashboard">
                <div className="dashboard-heading">
                    <h1>Diagram review</h1>
                    <p>Review animated diagrams for UK GCSE science and maths.</p>
                </div>
                <DashboardSummary diagrams={diagrams} />
                {storageError && (
                    <p className="storage-error" role="alert">Browser storage is unavailable. Reviews may be lost on refresh.</p>
                )}
                {diagrams.length ? (
                    <div className="table-container">
                        <table aria-label="GCSE diagrams">
                            <colgroup>
                                <col className="concept-col" />
                                <col className="preview-col" />
                                <col className="validation-col" />
                                <col className="generation-col" />
                                <col className="review-col" />
                            </colgroup>
                            <thead>
                                <tr>
                                    <th scope="col">Concept</th>
                                    <th scope="col">Animated preview</th>
                                    <th scope="col">Validation</th>
                                    <th scope="col">Generation</th>
                                    <th scope="col">Reviewer</th>
                                </tr>
                            </thead>
                            <tbody>
                                {diagrams.map((diagram) => (
                                    <DiagramRow
                                        key={diagram.concept.id}
                                        diagram={diagram}
                                        generation={generationByConcept[diagram.concept.id]}
                                        review={getReview(diagram)}
                                        onReview={(changes) => updateReview(diagram, changes)}
                                        onGenerate={() => handleGenerate(diagram)}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : <p className="storage-error">There are no concepts to review.</p>}
                <footer className="dashboard-footer">
                    Cost estimates use Gemini’s paid-tier rates. Reviews are saved in this browser.
                </footer>
            </main>
        </>
    );
}

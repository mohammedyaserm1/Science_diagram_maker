import { useRef, useState } from 'react';

const STORAGE_KEY = 'science_diagram_maker_reviews_v1';
const PENDING_REVIEW = { status: 'pending', notes: '' };

function readReviews() {
    try {
        const reviews = JSON.parse(localStorage.getItem(STORAGE_KEY));
        return reviews && typeof reviews === 'object' && !Array.isArray(reviews) ? reviews : {};
    } catch {
        return {};
    }
}

function revisionFor(diagram) {
    return diagram.generated_at ?? 'no-result';
}

export default function useReviews() {
    const [reviews, setReviews] = useState(readReviews);
    const [storageError, setStorageError] = useState(false);
    const latestReviews = useRef(reviews);

    function getReview(diagram) {
        return reviews[diagram.concept.id]?.[revisionFor(diagram)] ?? PENDING_REVIEW;
    }

    function updateReview(diagram, changes) {
        const conceptId = diagram.concept.id;
        const revision = revisionFor(diagram);
        const current = latestReviews.current;
        const next = {
            ...current,
            [conceptId]: {
                ...current[conceptId],
                [revision]: {
                    ...(current[conceptId]?.[revision] ?? PENDING_REVIEW),
                    ...changes,
                },
            },
        };
        latestReviews.current = next;
        setReviews(next);
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
            setStorageError(false);
        } catch {
            setStorageError(true);
        }
    }

    return { getReview, updateReview, storageError };
}

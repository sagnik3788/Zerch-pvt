#[rustfmt::skip]
pub struct CosineSimilarity {
    pub score: f32,
}
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> CosineSimilarity {
    if a.len() != b.len() {
        return CosineSimilarity { score: 0.0 };
    }

    let dot_product: f32 = a
        .iter()
        .zip(b.iter())
        .map(|(a_val, b_val)| a_val * b_val)
        .sum();

    #[rustfmt::skip]
    let norm = |v: &[f32]| {
        v.iter()
            .map(|v_val| v_val * v_val)
            .sum::<f32>()
            .sqrt()
    };

    let (norm_a, norm_b) = (norm(a), norm(b));

    if norm_a == 0.0 || norm_b == 0.0 {
        return CosineSimilarity { score: 0.0 };
    }

    CosineSimilarity {
        score: dot_product / (norm_a * norm_b),
    }
}

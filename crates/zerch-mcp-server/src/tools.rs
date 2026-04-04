use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::fs::File;
use std::io::Read;
use std::path::PathBuf;
use tokio::sync::Mutex;
use zerch_core::cosine_similarity;
use zerch_embed::LocalEmbedder;
use zerch_storage::VectorStore;

/// Shared application state for MCP tools.
pub struct AppState {
    pub embedder: Mutex<LocalEmbedder>,
    pub store_path: PathBuf,
}

impl AppState {
    pub fn new(embedder: LocalEmbedder, store_path: impl Into<PathBuf>) -> Self {
        Self {
            embedder: Mutex::new(embedder),
            store_path: store_path.into(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbedArgs {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbedResult {
    pub dimension: usize,
    pub vector: Vec<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchArgs {
    pub query: String,
    pub top_k: Option<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchHit {
    pub score: f32,
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub top_k: usize,
    pub hits: Vec<SearchHit>,
}

/// MCP tool: embed input text into a semantic vector.
pub async fn embed_text(state: &AppState, args: EmbedArgs) -> Result<EmbedResult> {
    let text = args.text.trim();
    if text.is_empty() {
        anyhow::bail!("`text` cannot be empty");
    }

    let mut embedder = state.embedder.lock().await;
    let vector = embedder
        .embed(text)
        .context("failed to generate embedding vector")?;

    let store = VectorStore::new(&state.store_path);
    store
        .append_vector(&vector, text)
        .context("failed to store embedded text in vector store")?;

    Ok(EmbedResult {
        dimension: vector.len(),
        vector,
    })
}

/// MCP tool: semantic search over `zerch_data.bin` using cosine similarity.
pub async fn search_logs(state: &AppState, args: SearchArgs) -> Result<SearchResult> {
    let query = args.query.trim();
    if query.is_empty() {
        anyhow::bail!("`query` cannot be empty");
    }

    let top_k = args.top_k.unwrap_or(5).max(1);

    let query_vector = {
        let mut embedder = state.embedder.lock().await;
        embedder
            .embed(query)
            .context("failed to embed search query")?
    };

    let mut file = File::open(&state.store_path).with_context(|| {
        format!(
            "failed to open vector store at {}",
            state.store_path.display()
        )
    })?;

    let mut candidates: Vec<SearchHit> = Vec::new();

    loop {
        let maybe_vec_len = read_u32_le(&mut file)?;
        let vec_len = match maybe_vec_len {
            Some(v) => v as usize,
            None => break, // clean EOF
        };

        let log_vector = read_f32_vec(&mut file, vec_len).context("failed to read stored vector")?;
        let text_len = read_u32_le(&mut file)?
            .context("unexpected EOF while reading text length")? as usize;
        let text = read_utf8_string(&mut file, text_len).context("failed to read stored text")?;

        let score = cosine_similarity(&query_vector, &log_vector).score;
        candidates.push(SearchHit { score, text });
    }

    candidates.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(Ordering::Equal));
    candidates.truncate(top_k);

    Ok(SearchResult {
        top_k,
        hits: candidates,
    })
}

/// Reads a little-endian u32. Returns:
/// - Ok(None) on EOF before any bytes are read (normal end of file),
/// - Ok(Some(value)) on success,
/// - Err on partial/truncated reads.
fn read_u32_le(file: &mut File) -> Result<Option<u32>> {
    let mut buf = [0u8; 4];
    let n = file.read(&mut buf)?;
    if n == 0 {
        return Ok(None);
    }
    if n < 4 {
        anyhow::bail!("corrupted store: truncated u32 field");
    }
    Ok(Some(u32::from_le_bytes(buf)))
}

fn read_f32_vec(file: &mut File, len: usize) -> Result<Vec<f32>> {
    let total = len
        .checked_mul(std::mem::size_of::<f32>())
        .context("vector length overflow while reading")?;
    let mut bytes = vec![0u8; total];
    file.read_exact(&mut bytes)?;

    let mut out = Vec::with_capacity(len);
    for chunk in bytes.chunks_exact(4) {
        out.push(f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]));
    }
    Ok(out)
}

fn read_utf8_string(file: &mut File, len: usize) -> Result<String> {
    let mut bytes = vec![0u8; len];
    file.read_exact(&mut bytes)?;
    Ok(String::from_utf8_lossy(&bytes).into_owned())
}

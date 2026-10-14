import * as store from './store.js';

let db = null;
let isCloudConnected = false;

/**
 * Initialize Firebase if config is available from the backend.
 * Falls back gracefully if no config or connection fails.
 */
export async function initFirebase() {
  try {
    const res = await fetch('/api/firebase-config');
    if (res.ok) {
      const config = await res.json();
      if (config && config.configured !== false) {
        // Dynamically load Firebase SDK to avoid blocking if unused
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js');
        const { getFirestore, collection, addDoc, getDocs, query, orderBy, limit, doc, getDoc } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js');
        
        const app = initializeApp(config);
        db = getFirestore(app);
        isCloudConnected = true;
        console.log("Firebase Cloud History Connected");
        return;
      }
    }
  } catch(e) {
    console.log("Firebase initialization skipped or failed:", e.message);
  }
  console.log("Using Local Session History");
}

export function isConnected() {
  return isCloudConnected;
}

/**
 * Save full analysis to Firestore, or fallback to localStorage.
 */
export async function saveAnalysisToHistory(analysis) {
  // Always save summary locally
  const summaryEntry = {
    analysisId: analysis.analysisId,
    datasetName: analysis.datasetName,
    createdAt: analysis.createdAt,
    records: analysis.summary.analysed,
    critical: analysis.summary.critical,
    high: analysis.summary.high,
    predictedFailures: analysis.summary.critical + analysis.summary.high,
    model: analysis.model,
    isDemo: analysis.isDemo,
    status: 'complete'
  };
  
  if (isCloudConnected && db) {
    try {
      const { collection, setDoc, doc } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js');
      await setDoc(doc(collection(db, "analyses"), analysis.analysisId), analysis);
      store.saveHistory(summaryEntry); // still keep local summary for fast list rendering
      return;
    } catch(e) {
      console.warn("Failed to save to Firestore, falling back to local full storage", e);
    }
  }
  
  // Fallback: save full analysis in a separate localStorage key to avoid bloating the summary list
  try {
    localStorage.setItem(`pdm.analysis_full.${analysis.analysisId}`, JSON.stringify(analysis));
  } catch(e) {
    console.warn("Could not save full analysis to localStorage (quota likely exceeded)");
  }
  store.saveHistory(summaryEntry);
}

/**
 * Retrieve full analysis from Firestore or localStorage.
 */
export async function getHistoricalAnalysis(analysisId) {
  if (isCloudConnected && db) {
    try {
      const { doc, getDoc } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js');
      const docSnap = await getDoc(doc(db, "analyses", analysisId));
      if (docSnap.exists()) {
        return docSnap.data();
      }
    } catch(e) {
      console.warn("Failed to fetch from Firestore", e);
    }
  }
  
  // Fallback to local full storage
  const raw = localStorage.getItem(`pdm.analysis_full.${analysisId}`);
  if (raw) return JSON.parse(raw);
  
  return null;
}

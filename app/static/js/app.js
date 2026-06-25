/* app.js – Fraud Detection Frontend Logic */

// ── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    document.getElementById("tab-single").classList.toggle("hidden", target !== "single");
    document.getElementById("tab-batch").classList.toggle("hidden",  target !== "batch");
  });
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function riskClass(risk) {
  return `risk-${risk}`;
}

function riskEmoji(risk) {
  return { LOW: "✅", MEDIUM: "⚠️", HIGH: "🔶", CRITICAL: "🚨" }[risk] || "❓";
}

function fraudColor(prob) {
  if (prob < 30)  return "#22c55e";
  if (prob < 60)  return "#f59e0b";
  if (prob < 90)  return "#fb923c";
  return "#ef4444";
}

function verdictText(isFraud) {
  return isFraud ? "FRAUDULENT 🚨" : "LEGITIMATE ✅";
}

function verdictColor(isFraud) {
  return isFraud ? "#ef4444" : "#22c55e";
}

// ── Single Prediction ─────────────────────────────────────────────────────────
const form       = document.getElementById("predictForm");
const submitBtn  = document.getElementById("submitBtn");
const clearBtn   = document.getElementById("clearBtn");
const demoBtn    = document.getElementById("demoBtn");
const resultPanel= document.getElementById("resultPanel");

form.addEventListener("submit", async e => {

  e.preventDefault();

  submitBtn.disabled = true;

  submitBtn.innerHTML = `<span class="spinner"></span> Analyzing…`;

  // Convert form values properly
  const formData = new FormData(form);

  const payload = {
    step: Number(formData.get("step")),
    type: formData.get("type"),
    amount: Number(formData.get("amount")),
    oldbalanceOrg: Number(formData.get("oldbalanceOrg")),
    newbalanceOrig: Number(formData.get("newbalanceOrig")),
    oldbalanceDest: Number(formData.get("oldbalanceDest")),
    newbalanceDest: Number(formData.get("newbalanceDest"))
  };

  console.log("Sending Data:", payload);

  try {

    const response = await fetch("/predict", {

      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify(payload)

    });

    const data = await response.json();

    console.log("Server Response:", data);

    // Show backend errors
    if (data.error) {

      alert("Backend Error: " + data.error);

      return;
    }

    renderResult(data);

  } catch (error) {

    console.error(error);

    alert("Network Error: " + error.message);

  } finally {

    submitBtn.disabled = false;

    submitBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      Analyze Transaction`;

  }

});

function renderResult(data) {

  console.log(data);

  const { fraud_probability, is_fraud, risk_level, confidence, threshold_used } = data;

  // header
  document.getElementById("resultIcon").textContent = is_fraud ? "🚨" : "✅";
  document.getElementById("resultTitle").textContent = is_fraud
    ? "Fraudulent Transaction Detected"
    : "Transaction Appears Legitimate";
  document.getElementById("resultTitle").style.color = verdictColor(is_fraud);
  document.getElementById("resultConfidence").textContent = confidence;

  const riskEl = document.getElementById("resultRisk");
  riskEl.textContent    = risk_level;
  riskEl.className      = `risk-badge ${riskClass(risk_level)}`;

  // stats
  document.getElementById("statProb").textContent    = fraud_probability + "%";
  document.getElementById("statProb").style.color    = fraudColor(fraud_probability);
  document.getElementById("statRisk").textContent    = risk_level;
  document.getElementById("statRisk").style.color    = fraudColor(fraud_probability);
  document.getElementById("statThresh").textContent  = threshold_used + "%";
  document.getElementById("statVerdict").textContent = verdictText(is_fraud);
  document.getElementById("statVerdict").style.color = verdictColor(is_fraud);

  // probability bar
  const fill   = document.getElementById("probBarFill");
  const marker = document.getElementById("probBarMarker");
  fill.style.width      = fraud_probability + "%";
  fill.style.background = `linear-gradient(90deg, #22c55e, ${fraudColor(fraud_probability)})`;
  marker.style.left     = threshold_used + "%";
  document.getElementById("probBarPct").textContent =
    `Fraud probability: ${fraud_probability}%  |  Threshold: ${threshold_used}%`;

  resultPanel.classList.remove("hidden");
  resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── Clear / Demo ──────────────────────────────────────────────────────────────
clearBtn.addEventListener("click", () => {
  form.reset();
  resultPanel.classList.add("hidden");
});

const DEMO_VALUES = {
  step: "206",
  type: "TRANSFER",
  amount: "9000.60",
  oldbalanceOrg: "9000.60",
  newbalanceOrig: "0.00",
  oldbalanceDest: "0.00",
  newbalanceDest: "0.00",
};

demoBtn.addEventListener("click", () => {
  Object.entries(DEMO_VALUES).forEach(([k, v]) => {
    const el = form.elements[k];
    if (el) el.value = v;
  });
  resultPanel.classList.add("hidden");
});

// ── Batch Analysis ────────────────────────────────────────────────────────────
const batchBtn     = document.getElementById("batchBtn");
const batchDemoBtn = document.getElementById("batchDemoBtn");
const batchInput   = document.getElementById("batchInput");
const batchResults = document.getElementById("batchResults");

const DEMO_BATCH = JSON.stringify([
  { step:1,  type:"TRANSFER", amount:181,    oldbalanceOrg:181,    newbalanceOrig:0,    oldbalanceDest:0,      newbalanceDest:0      },
  { step:10, type:"PAYMENT",  amount:500.50, oldbalanceOrg:5000,   newbalanceOrig:4499.50, oldbalanceDest:0,  newbalanceDest:0      },
  { step:206,type:"TRANSFER", amount:9000.6, oldbalanceOrg:9000.6, newbalanceOrig:0,    oldbalanceDest:0,      newbalanceDest:0      },
  { step:300,type:"CASH_OUT", amount:200000, oldbalanceOrg:200000, newbalanceOrig:0,    oldbalanceDest:12000,  newbalanceDest:212000 },
], null, 2);

batchDemoBtn.addEventListener("click", () => {
  batchInput.value = DEMO_BATCH;
});

batchBtn.addEventListener("click", async () => {
  let transactions;
  try {
    transactions = JSON.parse(batchInput.value);
  } catch {
    alert("Invalid JSON. Please check your input.");
    return;
  }

  batchBtn.disabled = true;
  batchBtn.innerHTML = `<span class="spinner"></span> Running…`;
  batchResults.innerHTML = "";
  batchResults.classList.add("hidden");

  try {
    const res  = await fetch("/batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(transactions),
    });
    const results = await res.json();

    batchResults.innerHTML = results.map(r => {
      if (r.error) return `<div class="batch-row"><span class="batch-idx">#${r.index}</span><span style="color:#ef4444">Error: ${r.error}</span></div>`;
      return `
        <div class="batch-row">
          <span class="batch-idx">#${r.index + 1}</span>
          <span class="bi">${r.is_fraud ? "🚨" : "✅"}</span>
          <span class="batch-pct" style="color:${fraudColor(r.fraud_probability)}">${r.fraud_probability}%</span>
          <span class="batch-verdict" style="color:${verdictColor(r.is_fraud)}">${verdictText(r.is_fraud)}</span>
          <span class="batch-risk ${riskClass(r.risk_level)}">${r.risk_level}</span>
        </div>`;
    }).join("");

    batchResults.classList.remove("hidden");
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    batchBtn.disabled = false;
    batchBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg> Run Batch Analysis`;
  }
});
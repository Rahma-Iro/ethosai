"""
EthosAI — Automated AI Ethics Auditing Tool
============================================
AI Skills Immersion Programme (AISIP) — Cohort 1
Pathway 2: AI Ethics & Governance

Deploy: streamlit run app.py
Requirements: pip install -r requirements.txt
"""

import streamlit as st
import re
import json
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EthosAI — AI Ethics Auditing Tool",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=Space+Mono&display=swap');

  html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

  /* ── Main background ── */
  .stApp { background: #F0F6F8; }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: #1A3C5E !important;
  }
  section[data-testid="stSidebar"] * { color: #E0EEF4 !important; }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stRadio label { color: #7EC8CE !important; font-weight: 600; }

  /* ── Risk badge colours ── */
  .badge-low    { background:#D1FAE5; color:#065F46; border:1.5px solid #059669; }
  .badge-medium { background:#FEF3C7; color:#92400E; border:1.5px solid #D97706; }
  .badge-high   { background:#FEE2E2; color:#991B1B; border:1.5px solid #DC2626; }
  .badge {
    display:inline-block; padding:3px 12px; border-radius:20px;
    font-size:13px; font-weight:700; font-family:'Space Mono', monospace;
  }

  /* ── Cards ── */
  .ethosai-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 14px;
    border-left: 5px solid #0E7C86;
    box-shadow: 0 2px 12px rgba(14,124,134,0.08);
  }
  .ethosai-card h4 { margin:0 0 6px 0; color:#1A3C5E; font-size:15px; }
  .ethosai-card p  { margin:0; color:#475569; font-size:13.5px; line-height:1.6; }

  .card-high   { border-left-color: #DC2626; }
  .card-medium { border-left-color: #D97706; }
  .card-low    { border-left-color: #059669; }

  /* ── Highlighted evidence spans ── */
  .evidence-phrase {
    background: #FEF08A;
    border-bottom: 2px solid #EAB308;
    border-radius: 3px;
    padding: 1px 3px;
    font-weight: 600;
  }
  .evidence-phrase-red {
    background: #FEE2E2;
    border-bottom: 2px solid #DC2626;
    border-radius: 3px;
    padding: 1px 3px;
    font-weight: 600;
  }

  /* ── Section headers ── */
  .section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 2.5px;
    color: #0E7C86; text-transform: uppercase; margin-bottom: 10px;
  }

  /* ── Score meter ── */
  .score-bar-wrap { background:#E2E8F0; border-radius:8px; height:10px; margin-top:6px; }
  .score-bar { height:10px; border-radius:8px; transition: width 0.6s ease; }

  /* ── Title hero ── */
  .hero-block {
    background: linear-gradient(135deg, #1A3C5E 0%, #0E7C86 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    color: white;
  }
  .hero-block h1 { font-size:38px; font-weight:700; margin:0 0 6px 0; color:white; }
  .hero-block p  { font-size:15px; color:#C8EBF0; margin:0; }

  /* ── Report export block ── */
  .report-block {
    background: #1A3C5E;
    color: white;
    border-radius: 12px;
    padding: 20px 24px;
  }
  .report-block h3 { color: #7EC8CE; margin-bottom:8px; }
  .report-block p  { color: #C8EBF0; font-size:13px; }

  /* ── Comparison mode ── */
  .compare-col {
    background: white;
    border-radius: 10px;
    padding: 18px;
    border: 1.5px solid #CBD5E1;
  }

  /* ── Footer ── */
  .footer-bar {
    text-align: center; color: #1A3C5E; font-size: 12px;
    padding: 20px 0 10px 0; border-top: 2px solid #0E7C86; margin-top: 40px;
  }
  .footer-bar small { color: #475569; font-size: 11px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ETHICS ANALYSIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Demographic bias patterns
BIAS_PATTERNS = {
    "gender": {
        "phrases": [
            r"\b(men are|women are|males are|females are|men tend|women tend|men perform|women perform)\b",
            r"\b(he is (more|less)|she is (more|less))\b",
            r"\b(typical(ly)? (male|female|man|woman))\b",
            r"\b(not suitable for (women|men))\b",
            r"\b(emotional(ly)?|irrational)\b.*\b(women|female)\b",
            r"\b(aggressive|dominant)\b.*\b(men|male)\b",
        ],
        "label": "Gender Bias",
        "description": "Language that assigns traits, abilities, or roles based on gender."
    },
    "ethnic": {
        "phrases": [
            r"\b(africans? (are|tend|always|never|usually))\b",
            r"\b(nigerians? (are|tend|always|never))\b",
            r"\b(these people|those people|such people)\b",
            r"\b(primitive|uncivilized|backward)\b",
            r"\b(naturally (lazy|aggressive|dishonest|untrustworthy))\b",
            r"\b(their kind|their type|their people)\b",
        ],
        "label": "Ethnic / Racial Bias",
        "description": "Language that stereotypes or generalizes about ethnic or racial groups."
    },
    "socioeconomic": {
        "phrases": [
            r"\bpoor people\b.{0,20}\b(are|always|never|tend)\b",
            r"\blow.?income\b.{0,40}\b(are|tend|cannot|should not|always|never)\b",
            r"\buneducated\b.{0,30}\b(are|tend|cannot)\b",
            r"\binformal sector workers?\b.{0,30}\b(are|cannot|should)\b",
            r"\b(they cannot afford|they lack the capacity)\b",
            r"\b(unbanked|underbanked) (individuals?|people|applicants?)\b.{0,30}\b(are|cannot|always|tend)\b",
        ],
        "label": "Socioeconomic Bias",
        "description": "Language that discriminates based on economic status or class."
    },
    "age": {
        "phrases": [
            r"\bolder workers?\b.{0,40}\b(are|cannot|struggle|fail|lack)\b",
            r"\byoung people\b.{0,30}\b(are|always|tend|cannot)\b",
            r"\btoo old\b.{0,20}\b(to|for)\b",
            r"\bmillennials?\b.{0,20}\b(are|always|never)\b",
            r"\bdigital natives?\b.{0,20}\b(are|can)\b",
            r"\bolder (applicants?|candidates?|employees?|workers?)\b",
            r"\b(age.related|age discrimination|ageist)\b",
        ],
        "label": "Age Bias",
        "description": "Language that assigns capability or suitability based on age."
    }
}

# Toxicity keyword groups
TOXICITY_PATTERNS = {
    "hate_speech": [
        r"\b(stupid|idiot|moron|imbecile)\b",
        r"\b(subhuman|inferior race|savages?)\b",
        r"\b(worthless (people|individuals|workers))\b",
        r"\b(scum|vermin|parasite)\b",
    ],
    "threatening": [
        r"\b(should be (eliminated|removed|expelled|banned))\b",
        r"\b(deserve(s?) (to suffer|punishment|nothing))\b",
        r"\b(must be stopped at all costs)\b",
    ],
    "derogatory": [
        r"\b(these (people|individuals) simply cannot)\b",
        r"\b(obviously (incapable|unable|unfit))\b",
        r"\b(inherently (inferior|superior|lazy|violent))\b",
    ],
    "pidgin_flags": [
        r"\b(dem no fit|e no dey|wetin dem)\b",
        r"\b(those ones no go)\b",
        r"\b(na so dem be)\b",
    ]
}

# Governance red flags
GOVERNANCE_PATTERNS = {
    "overclaiming_certainty": {
        "phrases": [
            r"\b(always accurate|100% accurate|100% reliable|100% correct|100% precise)\b",
            r"\bguaranteed\b.{0,20}\b(outcome|result|accuracy)\b",
            r"\b(infallible|cannot be wrong|cannot make mistakes)\b",
            r"definitively (proven?|proves?|shows?|demonstrates?|establishes?)",
            r"\bperfectly (predicts?|identifies?|assesses?|determines?)\b",
            r"\b(zero (error|mistake|bias|inaccuracy))\b",
            r"with (absolute|complete|total|full) (certainty|confidence|accuracy)",
        ],
        "label": "Certainty Overclaiming",
        "description": "AI systems should never claim 100% accuracy or guaranteed outcomes.",
        "remedy": "Replace absolute claims with probabilistic language (e.g., 'estimates', 'suggests', 'with X% confidence')."
    },
    "no_explainability": {
        "phrases": [
            r"\bthe (algorithm|model|system|AI) (decided|determined|concluded) (that|without)\b",
            r"\bbased on (proprietary|confidential|undisclosed) (data|criteria|factors)\b",
            r"\bthe (decision|outcome|result) cannot be (explained|disclosed|shared)\b",
            r"\bblack.?box (decision|system|outcome)\b",
            r"\bno (explanation|justification|reason) (will be|can be|is) (provided|given|shared)\b",
        ],
        "label": "Lack of Explainability",
        "description": "Decisions affecting individuals must be explainable, especially in regulated sectors.",
        "remedy": "Provide clear reasoning for all automated decisions. Reference specific factors that influenced the outcome."
    },
    "no_human_oversight": {
        "phrases": [
            r"\b(fully automated|no human (review|oversight|involvement|appeal))\b",
            r"\b(final (decision|verdict|determination) is made by (the AI|the system|the algorithm))\b",
            r"\b(human (review|oversight) is (not required|unnecessary|not available))\b",
            r"\bautomatically (rejected|approved|denied|disqualified) without\b",
        ],
        "label": "No Human Oversight",
        "description": "High-stakes AI decisions (hiring, credit, healthcare) require human review mechanisms.",
        "remedy": "Ensure all consequential decisions include a human review step and a right of appeal."
    },
    "data_privacy": {
        "phrases": [
            r"\b(personal (data|information) (will be|is) (shared|sold|disclosed|transferred) to)\b",
            r"\b(without (your|the user's) (consent|knowledge|permission))\b",
            r"\b(data (retention|storage) (period is|policy is) unlimited)\b",
            r"\bno (opt.out|right to (erasure|deletion|object))\b",
        ],
        "label": "Data Privacy Concern",
        "description": "AI systems must respect data rights, consent, and privacy regulations.",
        "remedy": "Specify data retention policies, consent mechanisms, and user rights clearly."
    }
}

# Sentiment disparity check — sample group terms
SENTIMENT_GROUPS = {
    "positive_words": r"\b(excellent|strong|reliable|capable|competent|trustworthy|ideal|outstanding|exceptional|skilled)\b",
    "negative_words": r"\b(risky|unreliable|incompetent|untrustworthy|weak|poor|inadequate|unsuitable|problematic|concerning)\b",
    "group_terms": {
        "women/female candidates": r"\b(women|female|she|her)\b",
        "men/male candidates":    r"\b(men|male|he|him|his)\b",
        "young applicants":       r"\b(young|junior|early.career|entry.level)\b",
        "older applicants":       r"\b(older|senior|experienced|mature)\b",
        "local applicants":       r"\b(Nigerian|local|domestic|African)\b",
        "foreign applicants":     r"\b(international|foreign|expatriate|overseas)\b",
    }
}

# Context-specific risk weightings
CONTEXT_WEIGHTS = {
    "Hiring & Recruitment": {
        "gender": 1.5, "ethnic": 1.5, "age": 1.4, "socioeconomic": 1.2,
        "no_human_oversight": 1.5, "overclaiming_certainty": 1.3,
        "sentiment_disparity": 1.4
    },
    "Credit Scoring & Finance": {
        "socioeconomic": 1.5, "ethnic": 1.3, "no_explainability": 1.6,
        "data_privacy": 1.5, "overclaiming_certainty": 1.4,
        "sentiment_disparity": 1.2
    },
    "Healthcare & Diagnosis": {
        "overclaiming_certainty": 1.8, "no_human_oversight": 1.8,
        "ethnic": 1.3, "gender": 1.2, "no_explainability": 1.5,
        "sentiment_disparity": 1.1
    },
    "Content Moderation": {
        "ethnic": 1.6, "gender": 1.4, "hate_speech": 1.5,
        "pidgin_flags": 1.5, "overclaiming_certainty": 1.2,
        "sentiment_disparity": 1.0
    },
    "General / Other": {
        "gender": 1.0, "ethnic": 1.0, "age": 1.0, "socioeconomic": 1.0,
        "no_human_oversight": 1.0, "overclaiming_certainty": 1.0,
        "sentiment_disparity": 1.0
    }
}


def find_matches(text, pattern_list):
    """Return list of (match_text, start, end) for all patterns."""
    found = []
    for pat in pattern_list:
        for m in re.finditer(pat, text, re.IGNORECASE):
            found.append((m.group(), m.start(), m.end()))
    return found


def score_risk(matches, weight=1.0, text_len=100):
    """Convert raw match count to a 0-100 risk score."""
    if not matches:
        return 0
    density = len(matches) / max(text_len / 100, 1)
    raw = min(density * 35 * weight, 100)
    return round(raw)


def risk_label(score):
    if score >= 55:
        return "HIGH", "high"
    elif score >= 25:
        return "MEDIUM", "medium"
    else:
        return "LOW", "low"


def analyze_bias(text, context):
    weights = CONTEXT_WEIGHTS.get(context, CONTEXT_WEIGHTS["General / Other"])
    results = {}
    all_evidence = []

    for key, cfg in BIAS_PATTERNS.items():
        matches = find_matches(text, cfg["phrases"])
        w = weights.get(key, 1.0)
        sc = score_risk(matches, w, len(text.split()))
        label, cls = risk_label(sc)
        results[key] = {
            "label": cfg["label"],
            "description": cfg["description"],
            "score": sc,
            "risk": label,
            "class": cls,
            "matches": [m[0] for m in matches],
        }
        all_evidence.extend(matches)

    return results, all_evidence


def analyze_toxicity(text, context):
    results = {}
    all_evidence = []
    weights = CONTEXT_WEIGHTS.get(context, CONTEXT_WEIGHTS["General / Other"])

    labels_map = {
        "hate_speech": ("Hate Speech", "Language targeting groups with hatred or contempt."),
        "threatening": ("Threatening Language", "Language that implies harm or threat."),
        "derogatory": ("Derogatory Language", "Language that demeans or belittles."),
        "pidgin_flags": ("Language Fairness (Pidgin)", "Nigerian Pidgin phrases often misclassified by standard models."),
    }

    for key, patterns in TOXICITY_PATTERNS.items():
        matches = find_matches(text, patterns)
        w = weights.get(key, 1.0)
        sc = score_risk(matches, w, len(text.split()))
        label, cls = risk_label(sc)
        lbl, desc = labels_map[key]
        results[key] = {
            "label": lbl,
            "description": desc,
            "score": sc,
            "risk": label,
            "class": cls,
            "matches": [m[0] for m in matches],
        }
        all_evidence.extend(matches)

    return results, all_evidence


def analyze_governance(text, context):
    results = {}
    all_evidence = []
    weights = CONTEXT_WEIGHTS.get(context, CONTEXT_WEIGHTS["General / Other"])

    for key, cfg in GOVERNANCE_PATTERNS.items():
        matches = find_matches(text, cfg["phrases"])
        w = weights.get(key, 1.0)
        sc = score_risk(matches, w, len(text.split()))
        label, cls = risk_label(sc)
        results[key] = {
            "label": cfg["label"],
            "description": cfg["description"],
            "remedy": cfg["remedy"],
            "score": sc,
            "risk": label,
            "class": cls,
            "matches": [m[0] for m in matches],
        }
        all_evidence.extend(matches)

    return results, all_evidence


def analyze_sentiment_disparity(text, context):
    """Check if positive/negative words are unevenly distributed across group mentions."""
    results = {}
    words = text.lower().split()
    total_words = max(len(words), 1)

    pos_matches = find_matches(text, [SENTIMENT_GROUPS["positive_words"]])
    neg_matches = find_matches(text, [SENTIMENT_GROUPS["negative_words"]])

    group_sentiment = {}
    for group_name, group_pat in SENTIMENT_GROUPS["group_terms"].items():
        g_mentions = find_matches(text, [group_pat])
        if not g_mentions:
            continue
        # Count sentiment words within 60 chars of each group mention
        pos_near = sum(
            1 for gm in g_mentions for pm in pos_matches
            if abs(gm[1] - pm[1]) < 60
        )
        neg_near = sum(
            1 for gm in g_mentions for nm in neg_matches
            if abs(gm[1] - nm[1]) < 60
        )
        group_sentiment[group_name] = {"positive": pos_near, "negative": neg_near, "mentions": len(g_mentions)}

    # Calculate disparity score
    if len(group_sentiment) < 2:
        return {"score": 0, "risk": "LOW", "class": "low",
                "label": "Sentiment Disparity", "group_sentiment": group_sentiment,
                "description": "Not enough group references to assess sentiment disparity."}

    sentiment_ratios = []
    for g, s in group_sentiment.items():
        total = s["positive"] + s["negative"]
        if total > 0:
            sentiment_ratios.append(s["positive"] / total)

    disparity = (max(sentiment_ratios) - min(sentiment_ratios)) * 100 if len(sentiment_ratios) >= 2 else 0
    w = CONTEXT_WEIGHTS.get(context, {}).get("sentiment_disparity", 1.0)
    score = round(min(disparity * w * 1.5, 100))
    label, cls = risk_label(score)

    return {
        "score": score, "risk": label, "class": cls,
        "label": "Sentiment Disparity",
        "description": "Unequal emotional tone applied to different demographic groups.",
        "group_sentiment": group_sentiment,
    }


def highlight_evidence(text, evidence_list, color="yellow"):
    """Return HTML with evidence phrases highlighted."""
    if not evidence_list:
        return f"<p style='color:#C8EBF0;font-size:14px;line-height:1.8'>{text}</p>"

    highlighted = text
    seen = set()
    for phrase, start, end in sorted(evidence_list, key=lambda x: -len(x[0])):
        if phrase.lower() in seen:
            continue
        seen.add(phrase.lower())
        css_class = "evidence-phrase-red" if color == "red" else "evidence-phrase"
        highlighted = re.sub(
            re.escape(phrase),
            f'<span class="{css_class}">{phrase}</span>',
            highlighted,
            flags=re.IGNORECASE,
            count=2
        )
    return f"<p style='color:#E0EEF4;font-size:14px;line-height:1.9;font-family:Georgia,serif'>{highlighted}</p>"


def compute_overall_score(bias_r, tox_r, gov_r, sent_r):
    """Weighted overall risk score."""
    all_scores = (
        [v["score"] for v in bias_r.values()] +
        [v["score"] for v in tox_r.values()] +
        [v["score"] for v in gov_r.values()] +
        [sent_r["score"]]
    )
    if not all_scores:
        return 0
    weighted = max(all_scores) * 0.4 + sum(all_scores) / len(all_scores) * 0.6
    return round(min(weighted, 100))


def generate_text_report(text_input, context, bias_r, tox_r, gov_r, sent_r, overall):
    """Generate a plain-text governance report."""
    now = datetime.now().strftime("%d %B %Y, %H:%M")
    label, _ = risk_label(overall)
    lines = [
        "=" * 65,
        "  ETHOSAI — AI ETHICS GOVERNANCE REPORT",
        "  Africa AI Hub | AI Skills Immersion Programme (AISIP)",
        "=" * 65,
        f"  Generated:      {now}",
        f"  Context:        {context}",
        f"  Overall Risk:   {label}  ({overall}/100)",
        "=" * 65,
        "",
        "SUBMITTED TEXT (first 200 characters):",
        f"  {text_input[:200]}{'...' if len(text_input) > 200 else ''}",
        "",
        "─" * 65,
        "1. BIAS DETECTION",
        "─" * 65,
    ]
    for k, v in bias_r.items():
        lines.append(f"  {v['label']:<30} {v['risk']:<8} (score: {v['score']}/100)")
        if v["matches"]:
            lines.append(f"    Evidence: {', '.join(v['matches'][:3])}")
    lines += ["", "─" * 65, "2. TOXICITY ANALYSIS", "─" * 65]
    for k, v in tox_r.items():
        lines.append(f"  {v['label']:<30} {v['risk']:<8} (score: {v['score']}/100)")
        if v["matches"]:
            lines.append(f"    Evidence: {', '.join(v['matches'][:3])}")
    lines += ["", "─" * 65, "3. GOVERNANCE FLAGS", "─" * 65]
    for k, v in gov_r.items():
        lines.append(f"  {v['label']:<30} {v['risk']:<8} (score: {v['score']}/100)")
        if v["matches"]:
            lines.append(f"    Evidence: {', '.join(v['matches'][:3])}")
        if v["risk"] != "LOW":
            lines.append(f"    Remedy: {v['remedy']}")
    lines += ["", "─" * 65, "4. SENTIMENT DISPARITY", "─" * 65]
    lines.append(f"  Sentiment Disparity      {sent_r['risk']:<8} (score: {sent_r['score']}/100)")
    lines += [
        "",
        "─" * 65,
        "IMPORTANT DISCLAIMER",
        "─" * 65,
        "  EthosAI is a screening tool, not a legal determination.",
        "  Results should be reviewed by a qualified ethics professional.",
        "  This tool does not access underlying model weights or training data.",
        "  False positives and false negatives are possible.",
        "",
        "  GitHub:     https://github.com/Rahma-Iro/ethosai/ethosai",
        "  Programme:  Africa AI Hub | AISIP Cohort 1",
        "=" * 65,
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ EthosAI")
    st.markdown("**AI Ethics Auditing Tool**")
    st.markdown("---")

    mode = st.radio("Mode", ["Single Text Audit", "Compare Two Texts"], index=0)
    st.markdown("---")

    context = st.selectbox(
        "📌 Deployment Context",
        ["Hiring & Recruitment", "Credit Scoring & Finance",
         "Healthcare & Diagnosis", "Content Moderation", "General / Other"],
        help="Context adjusts the risk weightings for each ethical dimension."
    )

    st.markdown("---")
    st.markdown("**About EthosAI**")
    st.markdown(
        "Built for the Africa AI Hub AISIP programme. "
        "Detects bias, toxicity, and governance gaps in AI-generated text — "
        "especially designed for Nigerian and African deployment contexts."
    )
    st.markdown("""
    <small>
    🌐 <a href='https://ethosai.streamlit.app' style='color:#7EC8CE'>ethosai.streamlit.app</a><br>
    💻 <a href='https://github.com/yourusername/ethosai' style='color:#7EC8CE'>github.com/yourusername/ethosai</a>
    </small>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("AISIP Cohort 1 | Pathway 2: AI Ethics & Governance")


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-block'>
  <h1>⚖️ EthosAI</h1>
  <p>Automated AI Ethics Auditing Tool &nbsp;·&nbsp; Africa AI Hub &nbsp;·&nbsp;
     Detects bias, toxicity & governance gaps in AI-generated content</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: render one full audit
# ─────────────────────────────────────────────────────────────────────────────
def render_audit(text_input, context, col_suffix=""):
    word_count = len(text_input.split())
    if word_count < 5:
        st.warning("⚠️  Please enter at least a few sentences for meaningful analysis.")
        return

    if word_count > 5000:
        st.warning("⚠️  Text exceeds 5,000 words. Only the first 5,000 words will be analyzed.")
        text_input = " ".join(text_input.split()[:5000])

    with st.spinner("🔍 Analyzing text across 5 ethical dimensions..."):
        bias_r,  bias_ev  = analyze_bias(text_input, context)
        tox_r,   tox_ev   = analyze_toxicity(text_input, context)
        gov_r,   gov_ev   = analyze_governance(text_input, context)
        sent_r             = analyze_sentiment_disparity(text_input, context)
        overall            = compute_overall_score(bias_r, tox_r, gov_r, sent_r)
        overall_label, overall_cls = risk_label(overall)

    # ── OVERALL SCORE ───────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Overall Risk Assessment</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        colour = {"LOW": "#059669", "MEDIUM": "#D97706", "HIGH": "#DC2626"}[overall_label]
        st.markdown(f"""
        <div style='background:{colour};color:white;border-radius:12px;padding:20px;text-align:center;'>
          <div style='font-size:42px;font-weight:700'>{overall}/100</div>
          <div style='font-size:16px;font-weight:600;letter-spacing:1px'>{overall_label} RISK</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style='background:#1A3C5E;border-radius:12px;padding:20px;border:1px solid #0E4D6B;height:100%'>
          <div style='font-size:13px;color:#7EC8CE;margin-bottom:4px;font-weight:600'>Context</div>
          <div style='font-size:15px;font-weight:700;color:#FFFFFF'>{context}</div>
          <div style='font-size:13px;color:#7EC8CE;margin-top:12px;margin-bottom:4px;font-weight:600'>Words analyzed</div>
          <div style='font-size:15px;font-weight:700;color:#FFFFFF'>{word_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        # Dimension summary
        all_dims = (
            list(bias_r.values()) + list(tox_r.values()) +
            list(gov_r.values()) + [sent_r]
        )
        high_count   = sum(1 for d in all_dims if d["risk"] == "HIGH")
        medium_count = sum(1 for d in all_dims if d["risk"] == "MEDIUM")
        low_count    = sum(1 for d in all_dims if d["risk"] == "LOW")
        st.markdown(f"""
        <div style='background:#1A3C5E;border-radius:12px;padding:20px;border:1px solid #0E4D6B;height:100%'>
          <div style='font-size:13px;color:#7EC8CE;margin-bottom:12px;font-weight:600'>Risk dimension summary</div>
          <div style='display:flex;gap:16px;align-items:center;flex-wrap:wrap;'>
            <span style='font-size:26px;font-weight:700;color:#DC2626'>{high_count}</span>
            <span style='font-size:13px;color:#C8EBF0;font-weight:600'>HIGH</span>
            <span style='font-size:26px;font-weight:700;color:#D97706;margin-left:10px'>{medium_count}</span>
            <span style='font-size:13px;color:#C8EBF0;font-weight:600'>MEDIUM</span>
            <span style='font-size:26px;font-weight:700;color:#34D399;margin-left:10px'>{low_count}</span>
            <span style='font-size:13px;color:#C8EBF0;font-weight:600'>LOW</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── FIVE DIMENSION SCORES (visual bars) ─────────────────────────────────
    st.markdown("<div class='section-label'>Risk Score by Dimension</div>", unsafe_allow_html=True)

    dim_summary = {
        "Demographic Bias": max(v["score"] for v in bias_r.values()),
        "Toxicity":         max(v["score"] for v in tox_r.values()),
        "Governance Flags": max(v["score"] for v in gov_r.values()),
        "Sentiment Disparity": sent_r["score"],
        "Language Fairness": tox_r.get("pidgin_flags", {}).get("score", 0),
    }

    bar_cols = st.columns(len(dim_summary))
    for col, (dim_name, dim_score) in zip(bar_cols, dim_summary.items()):
        dlabel, dcls = risk_label(dim_score)
        bar_colour = {"LOW": "#059669", "MEDIUM": "#D97706", "HIGH": "#DC2626"}[dlabel]
        with col:
            st.markdown(f"""
            <div style='background:#1A3C5E;border-radius:10px;padding:14px 12px;text-align:center;border:1px solid #0E4D6B;'>
              <div style='font-size:24px;font-weight:700;color:{bar_colour}'>{dim_score}</div>
              <div style='font-size:11px;color:#C8EBF0;margin:4px 0;font-weight:600'>{dim_name}</div>
              <div style='background:#0D2B43;border-radius:8px;height:10px;margin-top:6px;'>
                <div style='width:{max(dim_score,2)}%;height:10px;border-radius:8px;background:{bar_colour}'></div>
              </div>
              <span class='badge badge-{dcls}' style='margin-top:7px;display:inline-block'>{dlabel}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── NIGERIAN LANGUAGE VALIDATION NOTICE ─────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(90deg,#0E7C86 0%,#1A3C5E 100%);
         border-radius:10px;padding:14px 20px;margin:16px 0 4px 0;
         display:flex;align-items:center;gap:12px;'>
      <span style='font-size:22px'>🌍</span>
      <span style='color:#FFFFFF;font-size:13.5px;font-weight:600;'>
        Special validation on <u>Nigerian Pidgin English</u> &amp; <u>Yoruba-English code-switching</u>
        — closing the language fairness gap for African deployment contexts.
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── DETAILED RESULTS TABS ────────────────────────────────────────────────
    t1, t2, t3, t4, t5 = st.tabs([
        "⚖️ Bias Detection",
        "🛡️ Toxicity",
        "📋 Governance",
        "📊 Sentiment Disparity",
        "🔍 Evidence Highlights"
    ])

    with t1:
        st.markdown("<div class='section-label'>Demographic Bias Analysis</div>", unsafe_allow_html=True)
        for key, v in bias_r.items():
            with st.expander(f"{'🔴' if v['risk']=='HIGH' else '🟡' if v['risk']=='MEDIUM' else '🟢'}  {v['label']}  —  {v['risk']} ({v['score']}/100)"):
                st.markdown(f"**What this checks:** {v['description']}")
                st.markdown(f"""<div class='score-bar-wrap'><div class='score-bar'
                  style='width:{v["score"]}%;background:{"#DC2626" if v["risk"]=="HIGH" else "#D97706" if v["risk"]=="MEDIUM" else "#059669"}'></div></div>
                """, unsafe_allow_html=True)
                if v["matches"]:
                    st.markdown("**Flagged phrases:**")
                    for m in v["matches"][:5]:
                        st.markdown(f"- `{m}`")
                else:
                    st.success("No flagged phrases detected for this dimension.")

    with t2:
        st.markdown("<div class='section-label'>Toxicity & Harmful Language</div>", unsafe_allow_html=True)
        for key, v in tox_r.items():
            with st.expander(f"{'🔴' if v['risk']=='HIGH' else '🟡' if v['risk']=='MEDIUM' else '🟢'}  {v['label']}  —  {v['risk']} ({v['score']}/100)"):
                st.markdown(f"**What this checks:** {v['description']}")
                st.markdown(f"""<div class='score-bar-wrap'><div class='score-bar'
                  style='width:{v["score"]}%;background:{"#DC2626" if v["risk"]=="HIGH" else "#D97706" if v["risk"]=="MEDIUM" else "#059669"}'></div></div>
                """, unsafe_allow_html=True)
                if v["matches"]:
                    st.markdown("**Flagged phrases:**")
                    for m in v["matches"][:5]:
                        st.markdown(f"- `{m}`")
                else:
                    st.success("No toxic language detected for this dimension.")

    with t3:
        st.markdown("<div class='section-label'>AI Governance Red Flags</div>", unsafe_allow_html=True)
        for key, v in gov_r.items():
            with st.expander(f"{'🔴' if v['risk']=='HIGH' else '🟡' if v['risk']=='MEDIUM' else '🟢'}  {v['label']}  —  {v['risk']} ({v['score']}/100)"):
                st.markdown(f"**What this checks:** {v['description']}")
                if v["risk"] != "LOW":
                    st.info(f"💡 **Recommended remedy:** {v['remedy']}")
                st.markdown(f"""<div class='score-bar-wrap'><div class='score-bar'
                  style='width:{v["score"]}%;background:{"#DC2626" if v["risk"]=="HIGH" else "#D97706" if v["risk"]=="MEDIUM" else "#059669"}'></div></div>
                """, unsafe_allow_html=True)
                if v["matches"]:
                    st.markdown("**Flagged phrases:**")
                    for m in v["matches"][:5]:
                        st.markdown(f"- `{m}`")
                else:
                    st.success("No governance red flags detected for this dimension.")

    with t4:
        st.markdown("<div class='section-label'>Sentiment Disparity Across Groups</div>", unsafe_allow_html=True)
        st.markdown(f"**Overall disparity score:** `{sent_r['score']}/100` — "
                    f"<span class='badge badge-{sent_r['class']}'>{sent_r['risk']}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"*{sent_r['description']}*")

        if sent_r.get("group_sentiment"):
            st.markdown("**Sentiment breakdown by group mentioned in text:**")
            for group, sdata in sent_r["group_sentiment"].items():
                total = sdata["positive"] + sdata["negative"]
                if total == 0:
                    continue
                pos_pct = round(sdata["positive"] / total * 100)
                neg_pct = 100 - pos_pct
                st.markdown(f"""
                <div style='background:#1A3C5E;border-radius:8px;padding:12px 16px;
                     margin-bottom:8px;border:1px solid #0E4D6B;'>
                  <span style='color:#FFFFFF;font-weight:700;font-size:14px'>{group}</span>
                  <span style='color:#7EC8CE;font-size:13px'> — {sdata['mentions']} mention(s)</span><br>
                  <span style='color:#34D399'>●</span> <span style='color:#C8EBF0;font-size:13px'>Positive context: {pos_pct}%</span> &nbsp;
                  <span style='color:#F87171'>●</span> <span style='color:#C8EBF0;font-size:13px'>Negative context: {neg_pct}%</span>
                  <div style='background:#0D2B43;border-radius:8px;height:10px;margin-top:8px;overflow:hidden;display:flex;'>
                    <div style='width:{pos_pct}%;background:#059669'></div>
                    <div style='width:{neg_pct}%;background:#DC2626'></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Not enough group references found to assess sentiment disparity.")

    with t5:
        st.markdown("<div class='section-label'>Evidence Highlights in Submitted Text</div>", unsafe_allow_html=True)
        st.markdown("Flagged phrases are highlighted below. **Yellow** = bias/governance flag · **Red** = toxicity flag.")
        all_evidence = bias_ev + gov_ev
        toxic_evidence = tox_ev
        displayed = highlight_evidence(text_input[:3000], all_evidence + toxic_evidence, "yellow")
        st.markdown(f"<div style='background:#1A3C5E;padding:20px;border-radius:10px;border:1px solid #0E4D6B;max-height:400px;overflow-y:auto;color:#E0EEF4;font-size:14px;line-height:1.9;font-family:Georgia,serif'>{displayed}</div>",
                    unsafe_allow_html=True)
        if len(text_input) > 3000:
            st.caption("(Showing first 3,000 characters. Full text was analyzed.)")

    st.markdown("---")

    # ── EXPORT REPORT ───────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Export Governance Report</div>", unsafe_allow_html=True)
    report_text = generate_text_report(text_input, context, bias_r, tox_r, gov_r, sent_r, overall)
    st.download_button(
        label="⬇️  Download Governance Report (.txt)",
        data=report_text,
        file_name=f"EthosAI_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.caption("The report includes all risk scores, flagged phrases, remediation recommendations, and a disclaimer.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — SINGLE MODE
# ─────────────────────────────────────────────────────────────────────────────
if mode == "Single Text Audit":
    st.markdown("<div class='section-label'>Submit AI-Generated Text for Audit</div>", unsafe_allow_html=True)

    input_method = st.radio("Input method", ["Paste text", "Upload .txt file"], horizontal=True)

    text_input = ""
    if input_method == "Paste text":
        text_input = st.text_area(
            "Paste the AI-generated text here",
            height=220,
            placeholder="Paste any AI-generated content — hiring decision text, credit assessment report, healthcare triage output, content moderation ruling, etc.",
        )
    else:
        uploaded = st.file_uploader("Upload a .txt file", type=["txt"])
        if uploaded:
            text_input = uploaded.read().decode("utf-8", errors="replace")
            st.success(f"✅ File loaded: {uploaded.name} ({len(text_input.split())} words)")
            with st.expander("Preview uploaded text"):
                st.text(text_input[:500] + ("..." if len(text_input) > 500 else ""))

    run_btn = st.button("🔍  Run Ethics Audit", type="primary", use_container_width=True)

    if run_btn and text_input.strip():
        render_audit(text_input.strip(), context)
    elif run_btn:
        st.warning("Please enter or upload some text first.")

    # ── SAMPLE TEXTS ─────────────────────────────────────────────────────────
    with st.expander("🧪  Try a sample text"):
        samples = {
            "Biased Hiring Output": (
                "After reviewing all applications, we have determined that women are generally less suited "
                "for technical leadership roles due to their tendency to be more emotional and less analytical. "
                "The algorithm has definitively proven this based on proprietary data. Male candidates in the "
                "25–35 age range consistently outperform other groups. This is a fully automated decision "
                "and no human review is available. Older workers tend to struggle with the pace of innovation "
                "required in our environment."
            ),
            "Problematic Credit Assessment": (
                "The AI system has determined with 100% accuracy that this applicant poses a high default risk. "
                "Informal sector workers cannot be considered reliable borrowers. The decision is final and "
                "cannot be explained or appealed. Low-income individuals in Lagos always present higher risk "
                "profiles than their counterparts. This assessment is guaranteed to be correct."
            ),
            "Clean / Low Risk Example": (
                "Based on the applicant's financial history, debt-to-income ratio, and documented repayment "
                "record, our credit assessment model estimates a moderate risk level (65th percentile). "
                "This assessment is one input into a decision that will be reviewed by a qualified loan officer. "
                "The applicant has the right to request an explanation of the factors that contributed to this "
                "assessment and to appeal the final decision. The model was validated on Nigerian microfinance "
                "data and achieves 82% accuracy on held-out test data."
            ),
        }
        selected_sample = st.selectbox("Select a sample", list(samples.keys()))
        if st.button("Load this sample →"):
            st.session_state["sample_text"] = samples[selected_sample]
            st.rerun()

    if "sample_text" in st.session_state:
        st.text_area("Sample text loaded (scroll up and click Run Ethics Audit):",
                     value=st.session_state["sample_text"], height=120)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — COMPARE MODE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("<div class='section-label'>Compare Two AI Outputs Side by Side</div>", unsafe_allow_html=True)
    st.info("Submit outputs from two different AI systems (or two versions of the same system) to compare their ethical risk profiles.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**System A**")
        text_a = st.text_area("AI System A output", height=200, key="compare_a",
                               placeholder="Paste output from AI System A...")
    with col_b:
        st.markdown("**System B**")
        text_b = st.text_area("AI System B output", height=200, key="compare_b",
                               placeholder="Paste output from AI System B...")

    if st.button("🔍  Compare Both Systems", type="primary", use_container_width=True):
        if text_a.strip() and text_b.strip():
            ca, cb = st.columns(2)
            with ca:
                st.markdown("### System A Results")
                render_audit(text_a.strip(), context, col_suffix="_a")
            with cb:
                st.markdown("### System B Results")
                render_audit(text_b.strip(), context, col_suffix="_b")
        else:
            st.warning("Please enter text for both systems.")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='footer-bar'>
  <b>EthosAI</b> &nbsp;·&nbsp; Africa AI Hub &nbsp;·&nbsp; AISIP Cohort 1 &nbsp;·&nbsp;
  Pathway 2: AI Ethics & Governance &nbsp;·&nbsp; May 2026<br>
  <small>⚠️ EthosAI is a screening tool, not a legal determination. Results should be reviewed by a qualified ethics professional.
  This tool does not access underlying model weights or training data.</small>
</div>
""", unsafe_allow_html=True)

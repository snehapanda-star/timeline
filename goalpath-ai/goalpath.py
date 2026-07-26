import os
import json
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# Session cookie settings so history works reliably on hosted domains.
# GitHub Pages-style hosting / reverse proxies can otherwise drop cookies.
app.config.update(
  SESSION_COOKIE_SAMESITE=os.getenv("FLASK_SESSION_SAMESITE", "Lax"),
  SESSION_COOKIE_SECURE=os.getenv("FLASK_SESSION_SECURE", "false").lower() == "true",
)

client = AzureOpenAI(
  azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
)


def _build_prompt(payload: dict) -> str:
  goal_title = payload.get("goalTitle", "")
  goal_desc = payload.get("goalDesc", "")
  weekly_hours = payload.get("weeklyHours", 0)
  target_weeks = payload.get("targetWeeks", 0)
  constraints = payload.get("constraints", "")
  skills = payload.get("skills", "")
  weaknesses = payload.get("weaknesses", "")
  learning_style = payload.get("learningStyle", "")

  return (
    "You are an expert learning coach. Create a practical, week-by-week plan. "
    "Return ONLY valid JSON (no markdown). Keep it concise. "
    "Return ONLY valid JSON with this schema:\n"
    "{\n"
    '  "meta": {"goalTitle": string, "goalDesc": string, "weeklyHours": number, "targetWeeks": number, "constraints": string, "skills": string, "weaknesses": string, "learningStyle": string},\n'
    '  "weeks": [\n'
    "    {\n"
    "      \"week\": number,\n"
    "      \"goal\": string,\n"
    "      \"focus\": [ {\"text\": string, \"readMore\": string|null} ],\n"
    "      \"success\": string\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Rules:\n"
    "- weeks length must equal targetWeeks (clamp to 4..104).\n"
    "- focus must have exactly 3 items per week.\n"
    "- readMore should be a real URL or null.\n"
    "- success must be measurable (what the learner can produce/verify).\n\n"
    "Input:\n"
    f"Goal title: {goal_title}\n"
    f"Goal description: {goal_desc}\n"
    f"Weekly hours: {weekly_hours}\n"
    f"Target weeks: {target_weeks}\n"
    f"Constraints: {constraints}\n"
    f"Current skills/qualities: {skills}\n"
    f"Skills to improve: {weaknesses}\n"
    f"Learning style: {learning_style}\n"
  )


@app.post("/api/generate-timeline")
def generate_timeline():
  payload = request.get_json(force=True, silent=True) or {}
  target_weeks = int(payload.get("targetWeeks", 12) or 12)
  target_weeks = max(4, min(104, target_weeks))
  payload["targetWeeks"] = target_weeks

  prompt = _build_prompt(payload)
  model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")

  resp = client.chat.completions.create(
    model=model,
    messages=[
      {"role": "system", "content": "Return only valid JSON."},
      {"role": "user", "content": prompt},
    ],
  )
  content = resp.choices[0].message.content or "{}"
  try:
    plan = json.loads(content)
    print("Successfully parsed JSON from LLM response.")
    print(json.dumps(plan, indent=2))
  except json.JSONDecodeError:
    # Fallback: try to extract JSON substring
    start = content.find("{")
    end = content.rfind("}")
    plan = json.loads(content[start : end + 1]) if start != -1 and end != -1 else {"meta": payload, "weeks": []}

  return jsonify(plan)


@app.post("/api/coach")
def coach():
  payload = request.get_json(force=True, silent=True) or {}
  plan = payload.get("plan") or {}
  question = payload.get("question") or ""

  meta = plan.get("meta") or {}
  goal_title = meta.get("goalTitle", "")
  goal_desc = meta.get("goalDesc", "")
  weekly_hours = meta.get("weeklyHours", "")
  target_weeks = meta.get("targetWeeks", "")
  constraints = meta.get("constraints", "")
  skills = meta.get("skills", "")
  weaknesses = meta.get("weaknesses", "")
  learning_style = meta.get("learningStyle", "")

  model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")

  system = (
    "You are an expert learning coach. Answer the user's question with a practical, actionable plan. "
    "Be concise. Use bullet points when helpful."
  )

  user = (
    "Context (goal + timeline):\n"
    f"Goal title: {goal_title}\n"
    f"Goal description: {goal_desc}\n"
    f"Weekly hours: {weekly_hours}\n"
    f"Target weeks: {target_weeks}\n"
    f"Constraints: {constraints}\n"
    f"Current skills/qualities: {skills}\n"
    f"Skills to improve: {weaknesses}\n"
    f"Learning style: {learning_style}\n\n"
    "Timeline weeks (if available):\n"
    f"{json.dumps(plan.get('weeks', []), ensure_ascii=False)[:12000]}\n\n"
    "User question:\n"
    f"{question}\n\n"
    "Answer format:\n"
    "- Short answer (1-2 sentences)\n"
    "- What to do next (3-5 bullets)\n"
    "- How to measure success (1-2 bullets)\n"
  )

  resp = client.chat.completions.create(
    model=model,
    messages=[
      {"role": "system", "content": system},
      {"role": "user", "content": user},
    ],
  )

  content = resp.choices[0].message.content or ""
  return jsonify({"answer": content})


HOME_HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GoalPath AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#0b1220;
      --card:#0f1a2e;
      --text:#e5e7eb;
      --muted:#9ca3af;
      --primary:#dde2f5;
      --primary2:#dbf0f2;
      --border:rgba(255,255,255,.12);
      --shadow:0 20px 60px rgba(0,0,0,.35);
      --link:#a5b4fc;
    }

    /* Light mode overrides */
    body[data-theme="light"]{
      --bg:#f6f7fb;
      --card:#ffffff;
      --text:#0f172a;
      --muted:#475569;
      --primary:#4f46e5;
      --primary2:#06b6d4;
      --border:rgba(15,23,42,.12);
      --shadow:0 20px 60px rgba(2,6,23,.12);
      --link:#4f46e5;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family:"Plus Jakarta Sans", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background:linear-gradient(180deg,#070b14 0%, #0b1220 60%, #070b14 100%);
      color:var(--text);
    }

    body[data-theme="light"]{
      background:linear-gradient(180deg,#f8fafc 0%, #f6f7fb 60%, #f8fafc 100%);
    }
    .wrap{max-width:1100px;margin:0 auto;padding:28px 18px 60px}
    header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px}
    .brand{display:flex;align-items:center;gap:12px}
    .logo{
      width:42px;height:42px;border-radius:14px;
      background:linear-gradient(135deg,var(--primary),var(--primary2));
      box-shadow:0 18px 40px rgba(124,58,237,.25);
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:20px;
      line-height:1;
    }
    h1{font-size:18px;margin:0;letter-spacing:.2px}
    .sub{color:var(--muted);font-size:13px;margin-top:2px}

    .card{
      background:rgba(255,255,255,.04);
      border:1px solid var(--border);
      border-radius:18px;
      box-shadow:var(--shadow);
      backdrop-filter: blur(10px);
    }

    body[data-theme="light"] .card{
      background:rgba(255,255,255,.72);
    }

    .grid{
      display:grid;
      grid-template-columns: 1.1fr .9fr;
      gap:16px;
      align-items:start;
    }
    @media (max-width: 900px){.grid{grid-template-columns:1fr}}

    .wizardShell{padding:18px}
    .wizardTop{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
    .wizardTitle{font-size:16px;font-weight:700;margin:0}

    .wizardProgress{flex:1;display:flex;align-items:center;gap:10px}
    .bar{
      height:10px;border-radius:999px;background:rgba(255,255,255,.08);
      overflow:hidden;flex:1;border:1px solid rgba(255,255,255,.08)
    }
    .bar > i{display:block;height:100%;width:0%;background:linear-gradient(90deg,var(--primary),var(--primary2));transition:width .25s ease}
    .stepDots{display:flex;gap:8px}
    .dot{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.12)}
    .dot.active{background:linear-gradient(135deg,var(--primary),var(--primary2));border-color:rgba(255,255,255,.25)}

    .wizardGrid{display:grid;gap:14px}
    .wizardCard{padding:16px}

    label{display:block;font-size:13px;color:var(--muted);margin:10px 0 6px}
    .field input,.field textarea,.field select{
      width:100%;
      background:rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.12);
      color:var(--text);
      border-radius:14px;
      padding:12px 12px;
      outline:none;
    }
    .field textarea{min-height:92px;resize:vertical}

    #goalDesc{font-family:"Plus Jakarta Sans", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;}

    .wizardNavRow{display:flex;gap:10px;justify-content:flex-end;margin-top:14px}
    .btn{
      border-radius:14px;
      padding:10px 14px;
      border:1px solid rgba(255,255,255,.14);
      background:rgba(255,255,255,.06);
      color:var(--text);
      cursor:pointer;
      font-weight:700;
    }
    .btn:disabled{opacity:.55;cursor:not-allowed}
    .btn-primary{background:linear-gradient(135deg,var(--primary),var(--primary2));border-color:rgba(255,255,255,.18)}
    .btn-ghost{background:transparent}

    .previewPanel{padding:18px}
    .previewTitle{font-weight:800;margin-bottom:10px}
    .previewItem{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06)}
    .previewItem:last-of-type{border-bottom:none}
    .previewValue{color:var(--text);font-weight:700;text-align:right}
    .hr{height:1px;background:rgba(255,255,255,.10);margin:14px 0}
    .small{font-size:12px}
    .muted{color:var(--muted)}
    
    /* Ensure primary button text stays readable on dark button background */
    body:not([data-theme="light"]) .btn-primary{color:#0b1220}

    .reviewGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
    .reviewItem{padding:10px;border:1px solid rgba(255,255,255,.10);border-radius:14px;background:rgba(255,255,255,.03)}
    .reviewItem .muted{font-size:12px;margin-bottom:4px}
    .reviewValue{font-weight:800}

    .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
    .tabBtn{padding:10px 12px;border-radius:14px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.04);color:var(--text);cursor:pointer;font-weight:800}
    .tabBtn.active{background:linear-gradient(135deg,#2563eb,#60a5fa);border-color:rgba(37,99,235,.35);color:#0b1220}
    .tabPanel{padding:16px;border-top:1px solid rgba(255,255,255,.08)}

    /* Make dropdown selected text white in dark mode */
    body:not([data-theme="light"]) select{color:#e5e7eb;}

    .timeline{margin-top:10px}
    .phase{border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:12px;margin:10px 0;background:rgba(255,255,255,.03)}
    .phase h3{margin:0 0 6px;font-size:14px}
    .phase ul{margin:0;padding-left:18px;color:var(--muted)}

    footer{margin-top:18px;text-align:center;color:var(--muted)}

    /* Theme toggle */
    .themeToggle{
      display:flex;
      align-items:center;
      gap:10px;
      margin-left:auto;
      z-index:5;
    }
    .toggleBtn{
      border-radius:14px;
      padding:10px 12px;
      border:1px solid rgba(255,255,255,.14);
      background:rgba(255,255,255,.06);
      color:var(--text);
      cursor:pointer;
      font-weight:800;
      white-space:nowrap;
    }
    body[data-theme="light"] .toggleBtn{
      border-color:rgba(15,23,42,.14);
      background:rgba(15,23,42,.04);
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">
        <div class="logo" aria-hidden="true">🏆</div>
        <div>
          <h1>GoalPath - AI Timeline Generator</h1>
          <div class="sub">From vision to timeline in one click.</div>
        </div>
      </div>

      <div class="themeToggle" aria-label="Theme toggle">
        <button class="toggleBtn" id="themeToggle" type="button" aria-pressed="false">Toggle theme</button>
      </div>
    </header>

    <div class="grid">
      <div class="card wizardShell">
        <div class="wizardTop">
          <div class="wizardTitle">Onboarding</div>
          <div class="wizardProgress" aria-label="Progress">
            <div class="bar" aria-hidden="true"><i id="progressFill"></i></div>
            <div class="stepDots" aria-hidden="true">
              <span class="dot" id="dot1"></span>
              <span class="dot" id="dot2"></span>
              <span class="dot" id="dot3"></span>
              <span class="dot" id="dot4"></span>
            </div>
          </div>
        </div>

        <div class="wizardGrid">
          <section class="wizardCard" id="step1Panel">
            <h2>1) Your goal</h2>
            <label for="goalTitle">Ultimate goal (title)</label>
            <div class="field"><input id="goalTitle" placeholder="e.g., Become job-ready as a data analyst" /></div>

            <label for="goalDesc">Goal description / what “done” means</label>
            <div class="field"><textarea id="goalDesc" placeholder="Describe deliverable, outcome, or definition of success."></textarea></div>

            <div class="wizardNavRow">
              <button class="btn btn-primary" id="nextBtn" type="button">Continue</button>
            </div>
          </section>

          <section class="wizardCard" id="step2Panel" style="display:none">
            <h2>2) Availability</h2>
            <label for="weeklyHours">Hours per week</label>
            <div class="field"><input id="weeklyHours" type="number" min="1" max="40" value="6" /></div>

            <label for="targetWeeks">Target duration (weeks)</label>
            <div class="field"><input id="targetWeeks" type="number" min="4" max="104" value="12" /></div>

            <label for="constraints">Obstacles / constraints (optional)</label>
            <div class="field"><input id="constraints" placeholder="e.g., limited time, no mentor, need portfolio" /></div>

            <div class="wizardNavRow">
              <button class="btn btn-ghost" id="backBtn" type="button">Back</button>
              <button class="btn btn-primary" id="nextBtn2" type="button">Continue</button>
            </div>
          </section>

          <section class="wizardCard" id="step3Panel" style="display:none">
            <h2>3) Skills</h2>
            <label for="skills">Current skills/qualities (comma-separated)</label>
            <div class="field"><input id="skills" placeholder="e.g., Excel, curiosity, writing, basic SQL" /></div>

            <label for="weaknesses">Skills to improve (comma-separated)</label>
            <div class="field"><input id="weaknesses" placeholder="e.g., SQL joins, statistics, storytelling" /></div>

            <label for="learningStyle">Preferred learning style (optional)</label>
            <div class="field">
              <select id="learningStyle">
                <option value="hands-on" selected>Hands-on projects</option>
                <option value="reading">Reading + notes</option>
                <option value="videos">Videos + practice</option>
                <option value="mentored">Mentored feedback</option>
              </select>
            </div>

            <div class="wizardNavRow">
              <button class="btn btn-ghost" id="backBtn2" type="button">Back</button>
              <button class="btn btn-primary" id="nextBtn3" type="button">Continue</button>
            </div>
          </section>

          <section class="wizardCard" id="step4Panel" style="display:none">
            <h2>4) Review</h2>

            <div class="reviewGrid">
              <div class="reviewItem"><div class="muted">Goal Title</div><div class="reviewValue" id="reviewGoalTitle">—</div></div>
              <div class="reviewItem"><div class="muted">Goal Description</div><div class="reviewValue" id="reviewGoalDesc">—</div></div>
              <div class="reviewItem"><div class="muted">Hours / week</div><div class="reviewValue" id="reviewWeeklyHours">—</div></div>
              <div class="reviewItem"><div class="muted">Target duration</div><div class="reviewValue" id="reviewTargetWeeks">—</div></div>
              <div class="reviewItem"><div class="muted">Constraints</div><div class="reviewValue" id="reviewConstraints">—</div></div>
              <div class="reviewItem"><div class="muted">Current skills</div><div class="reviewValue" id="reviewSkills">—</div></div>
              <div class="reviewItem"><div class="muted">Skills to improve</div><div class="reviewValue" id="reviewWeaknesses">—</div></div>
              <div class="reviewItem"><div class="muted">Learning style</div><div class="reviewValue" id="reviewLearningStyle">—</div></div>
            </div>

            <div class="wizardNavRow">
              <button class="btn btn-ghost" id="backBtn3" type="button">Back</button>
              <button class="btn btn-primary" id="generateBtn" type="button">Create My Roadmap</button>
            </div>
          </section>
        </div>
      </div>

      <aside class="card previewPanel" aria-label="Roadmap preview">
        <div class="previewTitle">Live preview</div>
        <div class="previewItem">Goal<div class="previewValue" id="pvGoalTitle">—</div></div>
        <div class="previewItem">Availability<div class="previewValue" id="pvAvailability">—</div></div>
        <div class="previewItem">Skills<div class="previewValue" id="pvSkills">—</div></div>
        <div class="previewItem">Learning style<div class="previewValue" id="pvLearningStyle">—</div></div>
        <div class="hr"></div>
        <div class="small muted">Coaching + speaking appear after you generate.</div>
      </aside>
    </div>

    <section class="card" id="postOnboarding" style="margin-top:16px;display:none" aria-labelledby="timeline-title">
      <div class="tabs" role="tablist" aria-label="Roadmap tabs">
        <button class="tabBtn active" type="button" data-tab="roadmap" id="tabRoadmap">Roadmap</button>
        <button class="tabBtn" type="button" data-tab="coach" id="tabCoach">AI Coach</button>
        <button class="tabBtn" type="button" data-tab="speaking" id="tabSpeaking">Speaking Practice</button>
        <button class="tabBtn" type="button" data-tab="history" id="tabHistory">History</button>
      </div>

      <div class="tabPanel" id="panelRoadmap">
        <h2 id="timeline-title">Timeline output</h2>
        <div class="small muted">Phases, milestones, tasks, and success metrics.</div>
        <div class="timeline" id="timeline"></div>
      </div>

      <div class="tabPanel" id="panelCoach" style="display:none">
        <h2>AI Coach</h2>
        <div class="qa">
          <label for="question">Ask: “How do I improve X?”</label>
          <div class="field"><textarea id="question" placeholder="e.g., How do I improve SQL joins and practice it weekly?"></textarea></div>
          <button class="btn btn-ghost" id="askBtn" type="button">Get answer</button>
          <div class="answer" id="answer" aria-live="polite">Generate a timeline first, then ask questions.</div>
        </div>
      </div>

      <div class="tabPanel" id="panelSpeaking" style="display:none">
        <h2>Speaking Practice</h2>
        <div class="videoBox">
          <p class="small muted" style="margin:0">Offline MVP: analysis is a placeholder unless you connect an AI/video service.</p>
          <label for="videoFile">Video upload (mp4/webm)</label>
          <div class="field"><input id="videoFile" type="file" accept="video/*" /></div>
          <label for="testPrompt">What should you say? (optional)</label>
          <div class="field"><textarea id="testPrompt" placeholder="Tell a 60-second story: problem → decision → impact → lesson learned."></textarea></div>
          <button class="btn btn-ghost" id="testBtn" type="button">Analyze speaking test</button>
          <div class="answer" id="testAnswer" aria-live="polite">Upload a video and click “Analyze speaking test”.</div>
          <div class="hr"></div>
          <button class="btn btn-ghost" id="applyWeaknessesBtn" type="button" disabled>Apply detected weaknesses to timeline</button>
          <div class="hint">If you don’t know what to improve, this can suggest weaknesses to add to your plan.</div>
        </div>
      </div>

      <div class="tabPanel" id="panelHistory" style="display:none">
        <h2>History</h2>
        <div class="small muted">Your last generated roadmaps (inputs + timeline). Stored in your browser session.</div>
        <div class="wizardNavRow" style="justify-content:flex-start;gap:10px;margin-top:12px">
          <button class="btn btn-ghost" id="refreshHistoryBtn" type="button" aria-label="Refresh history">↻ Refresh</button>
          <button class="btn btn-ghost" id="clearHistoryBtn" type="button">Clear history</button>
        </div>
        <div class="hr"></div>
        <div id="historyList" class="timeline"></div>
      </div>
    </section>

    <footer class="small muted">
      <div style="margin-top:6px">© <span id="year"></span> Sneha Panda</div>
    </footer>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);

    // --- Generator (rules-based mentor tone) ---
    function splitList(s){
      return String(s || '')
        .split(',')
        .map(x => x.trim())
        .filter(Boolean);
    }

    function pickOne(arr, fallback){
      return (arr && arr.length) ? arr[0] : fallback;
    }

    // LLM-generated plan is rendered by renderTimeline(plan)

    function renderTimeline(plan){
      const el = $('timeline');
      el.innerHTML = '';

      plan.weeks.forEach((w) => {
        const div = document.createElement('div');
        div.className = 'phase';
        div.innerHTML = `
          <h3>Week ${w.week}</h3>
          <div class="small muted" style="margin-top:6px">Goal:</div>
          <div style="font-weight:900;margin-bottom:8px">${w.goal}</div>

          <div class="small muted" style="margin:10px 0 6px">Focus on:</div>
          <ul>${w.focus.map(item => {
            const text = typeof item === 'string' ? item : item.text;
            const url = typeof item === 'string' ? null : item.readMore;
            const link = url
              ? ` <a href="${url}" target="_blank" rel="noopener noreferrer" style="color:var(--link);text-decoration:underline">read more</a>`
              : '';
            return `<li>${text}${link}</li>`;
          }).join('')}</ul>

          <div class="small muted" style="margin:10px 0 6px">Success looks like:</div>
          <div style="font-weight:800;color:var(--text)">${w.success}</div>
        `;
        el.appendChild(div);
      });
    }

    function mentorAnswer(plan, question){
      const meta = plan?.meta || {};
      const goalTitle = meta.goalTitle || 'your goal';
      const weakList = splitList(meta.weaknesses);
      const skillList = splitList(meta.skills);

      const focus = pickOne(weakList, 'the skill you want to improve');
      const current = pickOne(skillList, 'what you already know');

      const goalLower = String(goalTitle || '').toLowerCase();
      const isLawGoal = /lawyer|attorney|legal|corporate law|corporate lawyer|law school|bar exam/.test(goalLower);
      const focusLower = String(focus || '').toLowerCase();
      const isCodingFocus = /code|coding|program|programming|developer|javascript|python|sql|software|engineering/.test(focusLower);

      // If the user wants to become a lawyer, coding is usually not a core requirement.
      // We should explicitly acknowledge that and redirect to legal-specific skills.
      if(isLawGoal && isCodingFocus){
        const suggestedLegalSkills = [
          'legal research (case law + statutes)',
          'issue spotting and legal writing',
          'contract basics (especially corporate/commercial)',
          'reading comprehension of legal documents',
          'oral advocacy / client communication'
        ];

        const legalSkill = suggestedLegalSkills[0];
        const altSkill = suggestedLegalSkills[1];

        return [
          `Short answer: If your goal is to become a corporate lawyer, coding usually isn’t required. Instead, focus on legal research and legal writing—those are the core skills.` ,
          `Why it matters: Corporate law work is mostly reading, analyzing, and drafting (contracts, memos, and deal documents). Coding can be useful in niche roles, but it’s not the standard path to becoming a lawyer.`,
          `What to do this week (specific):`,
          `1) Legal research drill: pick one corporate topic (e.g., “share purchase agreement basics” or “board resolutions”). Find 2–3 authoritative sources and summarize them in 10 bullet points.`,
          `2) Legal writing drill: write a 1-page “issue-spotting memo” (Facts → Issue → Rule → Analysis → Conclusion) using your sources.`,
          `3) Contract reading: read a short sample clause set (e.g., definitions + representations & warranties) and rewrite 3 clauses in plain English so you can explain them to a non-lawyer.`,
          `Success looks like: you can explain the issue, cite the rule you used, and draft a clear memo/summary without relying on copy-paste.`,
          `Common mistake to avoid: spending weeks on tools/skills that don’t map to the lawyer workflow. Choose one legal skill to practice weekly and measure progress by output (memos, summaries, drafts).`
        ].join('\n\n');
      }

      // Vary advice so it doesn't repeat the same 3 actions every time.
      const qLower = String(question || '').toLowerCase();
      const wantsPlan = /plan|week|schedule|roadmap/.test(qLower);
      const wantsPractice = /practice|drill|exercise|workout/.test(qLower);
      const wantsResources = /resource|book|course|learn|study/.test(qLower);

      const variants = [
        {
          title: 'Practice + feedback loop',
          steps: [
            `Do a 25-minute focused drill on ${focus}. Stop mid-way and write down what confused you (2–3 bullets).`,
            `Do a 15-minute “fix pass”: use one reference (notes, docs, or an example) to correct the confusion and produce one clean output (a summary, solution, or draft).`,
            `Ask for feedback: share that output with one person and ask one specific question: “What would you change first?”`
          ],
          success: `Success looks like: you can produce a correct output faster than last time, and you can explain the fix you made.`
        },
        {
          title: 'Mini-project that matches the goal',
          steps: [
            `Pick a tiny deliverable that proves progress toward “${goalTitle}” (something you can finish in 60–90 minutes).`,
            `Build it with a constraint: only use what you already know (${current}) plus one improvement area (${focus}).`,
            `Write a 6-sentence “before/after” note: what was hard, what you changed, and what improved.`
          ],
          success: `Success looks like: you have a tangible artifact you can show, not just notes.`
        },
        {
          title: 'Research → synthesis',
          steps: [
            `Find 2 high-quality examples related to ${focus}. For each, extract: (1) the key idea, (2) the common pattern, (3) one mistake to avoid.`,
            `Synthesize into a one-page cheat sheet you can use immediately next time you practice.`,
            `Run one “transfer test”: apply the cheat sheet to a new problem/task and compare results.`
          ],
          success: `Success looks like: you can reuse the same pattern on a new task without starting from scratch.`
        }
      ];

      let chosen = variants[0];
      if(wantsPlan) chosen = variants[1];
      else if(wantsPractice) chosen = variants[0];
      else if(wantsResources) chosen = variants[2];

      return [
        `Short answer: To improve ${focus}, use a repeatable loop that produces an output you can review (not just more reading).`,
        `Why it matters: ${focus} improves fastest when you practice in a realistic way and then correct mistakes immediately. Your goal (“${goalTitle}”) moves faster when you can explain what you changed and why.`,
        `What to do this week (${chosen.title}):`,
        `1) ${chosen.steps[0]}`,
        `2) ${chosen.steps[1]}`,
        `3) ${chosen.steps[2]}`,
        `${chosen.success}`,
        `Common mistake to avoid: picking a broad focus and doing “random practice”. Pick one focus, produce one artifact, and iterate.`
      ].join('\n\n');
    }

    function answerQuestion(plan, question){
      // Keep the structure exactly as requested.
      return mentorAnswer(plan, question);
    }

    // --- Wizard ---
    const wizard = { step: 1, plan: null };

    function requiredForStep(step){
      if(step === 1) return ['goalTitle','goalDesc'];
      if(step === 2) return ['weeklyHours','targetWeeks'];
      if(step === 3) return ['skills','weaknesses'];
      return [];
    }

    function showStep(step){
      wizard.step = step;
      ['step1Panel','step2Panel','step3Panel','step4Panel'].forEach((id, idx) => {
        const n = idx + 1;
        $(id).style.display = n === step ? 'block' : 'none';
      });

      // progress
      const fill = $('progressFill');
      fill.style.width = `${((step-1)/3)*100}%`;
      ['dot1','dot2','dot3','dot4'].forEach((d, idx) => {
        $(d).classList.toggle('active', idx+1 <= step);
      });

      if(step === 4){
        updateReview();
      }
    }

    function updatePreview(){
      const goalTitle = $('goalTitle').value.trim() || '—';
      const weeklyHours = $('weeklyHours').value.trim() || '—';
      const targetWeeks = $('targetWeeks').value.trim() || '—';
      const skills = $('skills').value.trim() || '—';
      const learningStyle = $('learningStyle').value || '—';

      $('pvGoalTitle').textContent = goalTitle;
      $('pvAvailability').textContent = `${weeklyHours} hrs/week • ${targetWeeks} weeks`;
      $('pvSkills').textContent = skills;
      $('pvLearningStyle').textContent = learningStyle;
    }

    function updateReview(){
      $('reviewGoalTitle').textContent = $('goalTitle').value.trim() || '—';
      $('reviewGoalDesc').textContent = $('goalDesc').value.trim() || '—';
      $('reviewWeeklyHours').textContent = $('weeklyHours').value.trim() || '—';
      $('reviewTargetWeeks').textContent = $('targetWeeks').value.trim() || '—';
      $('reviewConstraints').textContent = $('constraints').value.trim() || '—';
      $('reviewSkills').textContent = $('skills').value.trim() || '—';
      $('reviewWeaknesses').textContent = $('weaknesses').value.trim() || '—';
      $('reviewLearningStyle').textContent = $('learningStyle').value || '—';
    }

    function showPostOnboarding(){
      $('postOnboarding').style.display = 'block';
      $('postOnboarding').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function initTabs(){
      const tabButtons = document.querySelectorAll('.tabBtn');
      tabButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
          tabButtons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          const tab = btn.getAttribute('data-tab');
          $('panelRoadmap').style.display = tab === 'roadmap' ? 'block' : 'none';
          $('panelCoach').style.display = tab === 'coach' ? 'block' : 'none';
          $('panelSpeaking').style.display = tab === 'speaking' ? 'block' : 'none';
          $('panelHistory').style.display = tab === 'history' ? 'block' : 'none';
        });
      });
    }

    async function apiHistoryList(){
      const res = await fetch('/api/history/list', { method: 'GET' });
      if(!res.ok) throw new Error('Failed to load history');
      return res.json();
    }

    async function apiHistoryAdd(item){
      const res = await fetch('/api/history/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
      });
      if(!res.ok) throw new Error('Failed to save history');
      return res.json();
    }

    async function apiHistoryClear(){
      const res = await fetch('/api/history/clear', { method: 'POST' });
      if(!res.ok) throw new Error('Failed to clear history');
      return res.json();
    }

    function renderHistory(history){
      const el = $('historyList');
      el.innerHTML = '';
      if(!history || history.length === 0){
        el.innerHTML = `<div class="phase"><div class="small muted">No history yet. Generate a roadmap first.</div></div>`;
        return;
      }

      history.forEach((item) => {
        const inputs = item.inputs || {};
        const title = inputs.goalTitle || 'Untitled goal';
        const createdAt = item.createdAt ? new Date(item.createdAt) : null;
        const when = createdAt && !isNaN(createdAt.getTime()) ? createdAt.toLocaleString() : '';

        const div = document.createElement('div');
        div.className = 'phase';
        div.innerHTML = `
          <h3 style="display:flex;justify-content:space-between;gap:10px;align-items:baseline">
            <span>${title}</span>
            <span class="small muted">${when}</span>
          </h3>
          <div class="small muted" style="margin-top:6px">${inputs.weeklyHours || '—'} hrs/week • ${inputs.targetWeeks || '—'} weeks</div>
          <div class="wizardNavRow" style="justify-content:flex-start;margin-top:10px">
            <button class="btn btn-primary" type="button" data-history-id="${item.id}">Load</button>
          </div>
        `;
        el.appendChild(div);
      });

      el.querySelectorAll('button[data-history-id]').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-history-id');
          const found = (history || []).find(x => x.id === id);
          if(!found) return;
          wizard.plan = found.plan;
          renderTimeline(found.plan);
          // also update wizard review fields
          const inputs = found.inputs || {};
          $('goalTitle').value = inputs.goalTitle || '';
          $('goalDesc').value = inputs.goalDesc || '';
          $('weeklyHours').value = inputs.weeklyHours ?? '';
          $('targetWeeks').value = inputs.targetWeeks ?? '';
          $('constraints').value = inputs.constraints || '';
          $('skills').value = inputs.skills || '';
          $('weaknesses').value = inputs.weaknesses || '';
          $('learningStyle').value = inputs.learningStyle || 'hands-on';
          updateReview();
          $('tabRoadmap').click();
        });
      });
    }

    function validateStep(step){
      const ids = requiredForStep(step);
      for(const id of ids){
        const v = $(id).value;
        if(v === undefined) return false;
        if(String(v).trim() === '') return false;
      }
      return true;
    }

    // wiring
    $('nextBtn').addEventListener('click', () => { if(!validateStep(1)) return; showStep(2); updatePreview(); });
    $('backBtn').addEventListener('click', () => showStep(1));

    $('nextBtn2').addEventListener('click', () => { if(!validateStep(2)) return; showStep(3); updatePreview(); });
    $('backBtn2').addEventListener('click', () => showStep(2));

    $('nextBtn3').addEventListener('click', () => { if(!validateStep(3)) return; showStep(4); updatePreview(); });
    $('backBtn3').addEventListener('click', () => showStep(3));

    async function generateTimelineFromApi(payload){
      const res = await fetch('/api/generate-timeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if(!res.ok){
        const text = await res.text().catch(() => '');
        throw new Error(`Request failed (${res.status}). ${text}`);
      }
      return res.json();
    }

    $('generateBtn').addEventListener('click', async () => {
      const generateBtn = $('generateBtn');
      generateBtn.disabled = true;
      const prevText = generateBtn.textContent;
      generateBtn.textContent = 'Generating...';

      try {
        const payload = {
          goalTitle: $('goalTitle').value.trim(),
          goalDesc: $('goalDesc').value.trim(),
          weeklyHours: Number($('weeklyHours').value),
          targetWeeks: Number($('targetWeeks').value),
          constraints: $('constraints').value.trim(),
          skills: $('skills').value.trim(),
          weaknesses: $('weaknesses').value.trim(),
          learningStyle: $('learningStyle').value
        };

        const plan = await generateTimelineFromApi(payload);
        wizard.plan = plan;
        renderTimeline(plan);
        showPostOnboarding();
        $('tabRoadmap').click();

        // Save to history
        const item = {
          id: `gp_${Date.now()}_${Math.random().toString(16).slice(2)}`,
          createdAt: new Date().toISOString(),
          inputs: payload,
          plan
        };
        await apiHistoryAdd(item);

        // Always refresh history after saving so the next time you open History
        // you immediately see all newly generated roadmaps.
        const h = await apiHistoryList();
        renderHistory(h.history);

        // Go to Roadmap tab after generating
        $('tabRoadmap').click();

        // (No need to condition on panel visibility; renderHistory updates the list.)
      } catch (err) {
        $('answer').textContent = `Error generating timeline: ${String(err?.message || err)}`;
      } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = prevText;
      }
    });

    $('clearHistoryBtn').addEventListener('click', async () => {
      try{
        await apiHistoryClear();
        const h = await apiHistoryList();
        renderHistory(h.history);
      }catch(e){
        // ignore
      }
    });

    const refreshBtn = $('refreshHistoryBtn');
    if(refreshBtn){
      refreshBtn.addEventListener('click', async () => {
        try{
          const h = await apiHistoryList();
          renderHistory(h.history);
        }catch(e){
          // ignore
        }
      });
    }

    $('askBtn').addEventListener('click', async () => {
      const q = $('question').value.trim();
      if(!q){ $('answer').textContent = 'Type a question first.'; return; }
      if(!wizard.plan){ $('answer').textContent = 'Generate a timeline first, then ask questions.'; return; }

      const askBtn = $('askBtn');
      const prev = askBtn.textContent;
      askBtn.disabled = true;
      askBtn.textContent = 'Thinking...';
      $('answer').textContent = '';

      try{
        const res = await fetch('/api/coach', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ plan: wizard.plan, question: q })
        });
        if(!res.ok){
          const t = await res.text().catch(() => '');
          throw new Error(`Request failed (${res.status}). ${t}`);
        }
        const data = await res.json();
        $('answer').textContent = data?.answer || 'No answer returned.';
      }catch(e){
        $('answer').textContent = `Error: ${String(e?.message || e)}`;
      }finally{
        askBtn.disabled = false;
        askBtn.textContent = prev;
      }
    });

    // init
    $('year').textContent = new Date().getFullYear();

    // --- Theme (dark/light) ---
    const THEME_KEY = 'goalpath_theme';
    const themeToggleBtn = $('themeToggle');

    function applyTheme(theme){
      const isLight = theme === 'light';
      document.body.setAttribute('data-theme', isLight ? 'light' : 'dark');
      themeToggleBtn.setAttribute('aria-pressed', String(isLight));
      themeToggleBtn.textContent = isLight ? 'Light mode' : 'Dark mode';
    }

    function getPreferredTheme(){
      const saved = localStorage.getItem(THEME_KEY);
      if(saved === 'light' || saved === 'dark') return saved;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    applyTheme(getPreferredTheme());

    themeToggleBtn.addEventListener('click', () => {
      const current = document.body.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next = current === 'light' ? 'dark' : 'light';
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    });

    initTabs();
    updatePreview();
    showStep(1);

    // On refresh: show post-onboarding UI, but don't force History tab.
    $('postOnboarding').style.display = 'block';

    // live preview updates
    ['goalTitle','weeklyHours','targetWeeks','skills','learningStyle'].forEach(id => {
      $(id).addEventListener('input', updatePreview);
      $(id).addEventListener('change', updatePreview);
    });
  </script>
</body>
</html>
'''


@app.get("/")
def index():
  return HOME_HTML


@app.post("/api/history/add")
def history_add():
  data = request.get_json(force=True, silent=True) or {}
  item = {
    "id": data.get("id"),
    "createdAt": data.get("createdAt"),
    "inputs": data.get("inputs"),
    "plan": data.get("plan"),
  }
  if not item.get("id"):
    return jsonify({"ok": False, "error": "missing id"}), 400

  # Ensure the payload is JSON-serializable.
  try:
    json.dumps(item.get("plan"), ensure_ascii=False)
  except Exception:
    item["plan"] = None

  # Store history in a simple in-memory list keyed by a fixed key.
  # This avoids Flask session/cookie issues on hosted domains.
  # NOTE: This is per-process; for multi-worker deployments, use a real DB.
  global _HISTORY
  try:
    _HISTORY
  except NameError:
    _HISTORY = []

  hist = [x for x in _HISTORY if x.get("id") != item["id"]]
  hist.insert(0, item)
  hist = hist[:10]
  _HISTORY = hist
  return jsonify({"ok": True, "item": item})


@app.get("/api/history/list")
def history_list():
  global _HISTORY
  try:
    hist = _HISTORY
  except NameError:
    hist = []
  return jsonify({"ok": True, "history": hist})


@app.post("/api/history/clear")
def history_clear():
  global _HISTORY
  _HISTORY = []
  return jsonify({"ok": True})

if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=True)
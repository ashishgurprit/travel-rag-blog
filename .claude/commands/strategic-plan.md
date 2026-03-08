---
description: Strategic planning with 3D Decision Matrix — C-Suite perspectives, Six Thinking Hats, and SPADE framework
allowed-tools: ["Read", "Bash", "Glob"]
---
# Strategic Planning with 3D Decision Matrix

> Systematic planning using C-Suite perspectives, Six Thinking Hats, and proven decision frameworks

## When to Use This Skill

Use this skill when you need to:
- Plan complex features or architectural changes
- Make high-stakes technical or product decisions
- Evaluate multiple approaches systematically
- Align technical work with strategic objectives
- Navigate decisions that affect multiple stakeholders

**DO NOT use this skill for**:
- Simple bug fixes or trivial changes
- Decisions that have already been made
- Pure implementation work (use `/project:implement` instead)

## Core Framework: The 3D Decision Matrix

This skill integrates three powerful dimensions:

### Dimension 1: C-Suite Perspectives (WHO)
Every decision is viewed through multiple strategic lenses:
- **CEO**: Vision, strategy, culture alignment
- **CTO**: Technical architecture, scalability, maintainability
- **CPO**: User experience, product fit, usability
- **CFO**: Resource efficiency, ROI, cost-effectiveness
- **COO**: Operational reliability, execution, delivery
- **CRO**: User adoption, value delivery, success metrics

### Dimension 2: Six Thinking Hats (HOW)
Structured cognitive exploration:
- **⚪ White Hat**: Facts, data, information gathering
- **🔴 Red Hat**: Intuition, emotions, gut feelings
- **⚫ Black Hat**: Risks, concerns, potential failures
- **🟡 Yellow Hat**: Benefits, value, opportunities
- **🟢 Green Hat**: Creativity, alternatives, possibilities
- **🔵 Blue Hat**: Process control, synthesis, decisions

### Dimension 3: Decision Framework (WHAT & WHEN)
Classification-driven process selection:
- **Trapdoor Decisions** (irreversible): Full SPADE + commitment
- **High-Stakes Decisions** (important): Quick SPADE + key perspectives
- **Low-Stakes Decisions** (reversible): Bias for action + sanity check

## Decision Process

### Step 1: Classify the Decision

**Use the classifier script first:**
```bash
python scripts/classify_decision.py "decision description"
```

Or classify manually:
- **Is it reversible?** (Can we change it later easily?)
- **Is it important?** (Does it affect architecture, users, or strategy?)
- **Is it a trapdoor?** (Name, API, core architecture, public contracts?)

**Decision Matrix:**
```
                    REVERSIBILITY
          ┌─────────────────┬─────────────────┐
          │   TWO-WAY DOOR  │   ONE-WAY DOOR  │
┌─────────┼─────────────────┼─────────────────┤
│  HIGH   │   THOUGHTFUL    │    TRAPDOOR     │
│         │   Quick SPADE   │   Full SPADE    │
├─────────┼─────────────────┼─────────────────┤
│  LOW    │     YOLO        │    VERIFY       │
│         │   Just do it    │   Quick check   │
└─────────┴─────────────────┴─────────────────┘
```

### Step 2: Select Perspectives

**Primary + Secondary C-Suite Roles:**
- Vision/Strategy → CEO
- Technical → CTO
- User Experience → CPO
- Resources → CFO
- Operations → COO
- Adoption → CRO

**Select based on decision domain:**
- Architecture decision: CTO + COO
- Feature planning: CPO + CRO
- Tool selection: CTO + CFO
- Process change: COO + CEO

### Step 3: Apply Thinking Hats

**Hat sequences by decision type:**

**Trapdoor (full deliberation):**
🔵 Blue → ⚪ White → 🟢 Green → 🟡 Yellow → ⚫ Black → 🔴 Red → 🔵 Blue

**High-stakes creative:**
⚪ White → 🟢 Green → 🟡 Yellow → ⚫ Black → 🔴 Red

**Risk assessment:**
⚪ White → ⚫ Black → 🟢 Green → 🟡 Yellow

**Quick tactical:**
⚪ White → 🔴 Red

**For each hat, ask the perspective-specific questions:**
- ⚪ + CTO: What are the technical facts?
- 🔴 + CEO: Does this feel strategically right?
- ⚫ + COO: What operational risks exist?
- 🟡 + CPO: What user value does this create?
- 🟢 + CTO: What technical alternatives exist?
- 🔵 + COO: What's the execution process?

### Step 4: Execute Decision Framework

#### For TRAPDOOR Decisions (Full SPADE)

**S - Setting:**
- What decision are we making?
- Why is it important?
- What context matters?
- What constraints exist?

**P - People:**
- Who is **Responsible** (owns the decision)?
- Who must **Approve** (has veto power)?
- Who are **Consultants** (provide input)?
- Who gets **Informed** (needs to know)?

**A - Alternatives:**
- List 3-5 viable options
- For each option:
  - **Pros** (Yellow Hat findings)
  - **Cons** (Black Hat findings)
  - **Technical feasibility** (CTO perspective)
  - **User impact** (CPO perspective)
  - **Resource cost** (CFO perspective)

**D - Decide:**
- Select the option
- State clear rationale
- Reference hat insights that drove the decision

**E - Explain:**
- Document the decision
- Explain to all stakeholders
- Commit fully (disagree & commit principle)

#### For HIGH-STAKES Decisions (Quick SPADE)

- Abbreviated Setting (1-2 sentences)
- Assign owner (single role)
- List 2-3 key alternatives
- Decide with brief rationale
- Document decision

#### For LOW-STAKES Decisions (Bias for Action)

- Gather facts (White Hat)
- Quick gut check (Red Hat)
- Sanity check risks (Black Hat)
- Decide and move forward
- Document briefly

### Step 5: Commit and Document

**Amazon Principle: Disagree and Commit**
- Encourage open disagreement during deliberation
- Once decided, everyone commits fully
- No second-guessing or undermining

**Documentation Template:**
```markdown
## Decision: [Title]

**Date:** [YYYY-MM-DD]
**Type:** [Trapdoor|High-Stakes|Low-Stakes]
**Perspectives:** [Primary + Secondary]

### Context
[What decision and why]

### Alternatives Considered
1. [Option 1] - [Brief pros/cons]
2. [Option 2] - [Brief pros/cons]
3. [Option 3] - [Brief pros/cons]

### Decision
[Selected option and rationale]

### Key Insights
- ⚪ White: [Facts that mattered]
- ⚫ Black: [Risks acknowledged]
- 🟡 Yellow: [Benefits expected]
- 🔴 Red: [Gut check result]

### Commitment
All stakeholders commit to this decision.
```

## Example: Planning a New Feature

**Scenario:** Adding real-time collaboration to a document editor

### 1. Classify Decision
- **Reversibility:** ONE-WAY (affects architecture deeply)
- **Importance:** HIGH (major feature, affects UX and scalability)
- **Type:** TRAPDOOR (architectural choice is hard to reverse)
- **Process:** Full SPADE with all hats

### 2. Select Perspectives
- **Primary:** CTO (technical architecture)
- **Secondary:** CPO (user experience)
- **Consult:** CFO (infrastructure cost), COO (operational complexity)

### 3. Apply Thinking Hats

**🔵 Blue (Process):**
"We need to decide: WebSockets vs Server-Sent Events vs Polling for real-time sync"

**⚪ White (Facts - CTO):**
- Current tech stack: Node.js backend, React frontend
- Expected concurrent users: 100-1000
- Average document size: 10-50KB
- Network latency requirements: <100ms sync time

**🟢 Green (Alternatives - CTO + CPO):**
1. **WebSockets (Socket.io)**
   - Bidirectional, persistent connection
   - Best performance for high-frequency updates

2. **Server-Sent Events (SSE)**
   - Unidirectional, simpler than WebSockets
   - Good for updates flowing server→client

3. **Long Polling with Operational Transform**
   - Fallback compatible, works everywhere
   - Higher latency, more server load

**🟡 Yellow (Benefits):**
- WebSockets: Real-time UX, handles 1000+ concurrent users
- SSE: Simpler implementation, good enough for <100 users
- Polling: Maximum compatibility, no special server requirements

**⚫ Black (Risks - CTO + COO):**
- WebSockets: Complex state management, sticky sessions needed, harder ops
- SSE: Unidirectional limits some use cases, browser compatibility gaps
- Polling: High server load, poor UX under load, scalability ceiling

**🔴 Red (Gut Check - CEO + CPO):**
- "Real-time collab is a competitive differentiator - invest in best UX"
- "WebSockets feels right for a collaboration feature"

### 4. Execute SPADE

**Setting:**
Choose real-time sync architecture for collaborative document editing. This is a one-way door decision that affects scalability, UX, and operational complexity for years.

**People:**
- Responsible: CTO
- Approver: CEO
- Consultants: CPO, COO, CFO
- Informed: Engineering team

**Alternatives:**
1. **WebSockets** ✓
   - Pros: Best UX, scales to 1000+ users, bidirectional
   - Cons: Complex ops, requires sticky sessions, higher dev cost

2. **SSE**
   - Pros: Simpler, adequate for current scale
   - Cons: Unidirectional, may need replacement if scale grows

3. **Polling**
   - Pros: Simple, compatible
   - Cons: Poor UX, doesn't scale

**Decision:** WebSockets (Socket.io)

**Rationale:**
- Real-time collaboration is a core differentiator (CEO perspective)
- Scalability headroom justifies upfront complexity (CTO perspective)
- Superior UX creates competitive advantage (CPO perspective)
- Infrastructure cost is acceptable given strategic value (CFO perspective)

**Explain:**
We're committing to WebSockets for real-time sync. Yes, it's more complex operationally, but the UX and scalability benefits align with our strategic direction. All engineering work will assume WebSockets from now on.

### 5. Commit

**Commitment:**
All stakeholders agree to WebSockets. No second-guessing. We'll handle the operational complexity because the strategic benefits are clear.

## Tips for Effective Use

### When to Use Full Process
- Naming APIs, skills, or public interfaces
- Choosing frameworks or core dependencies
- Architectural patterns that touch multiple systems
- Product decisions that affect all users
- Anything expensive or time-consuming to reverse

### When to Use Quick Process
- Implementation details within an agreed architecture
- Tool selection for internal use
- Process improvements
- Non-critical feature decisions

### When to Just Decide
- Code formatting choices
- Variable naming
- File organization
- Asset selection
- Documentation structure (unless public API docs)

### Common Pitfalls
- **Analysis paralysis:** Not every decision needs full deliberation
- **Skipping classification:** Always classify first - saves time
- **Solo perspective:** Always use at least 2 C-Suite perspectives
- **Hat skipping:** Don't skip Black Hat (risks) or White Hat (facts)
- **Failure to commit:** Disagreement during is good; after is toxic

### Integration with Existing Workflows

**With `/project:plan`:**
Use strategic-plan for the high-level decisions, then `/project:plan` for implementation details.

**With `/project:implement`:**
Make architectural decisions with strategic-plan first, then implement with confidence.

**With `/project:review`:**
Reference strategic-plan decisions in code review to explain "why" choices were made.

## References

See `references/` directory for:
- Full 3D Decision Matrix documentation
- SPADE framework deep-dive
- Six Thinking Hats detailed guide
- C-Suite perspective mapping
- Decision classification examples

## Output Format

When using this skill, structure your planning as:

```markdown
# Strategic Plan: [Feature/Decision Name]

## Decision Classification
- Type: [Trapdoor|High-Stakes|Low-Stakes]
- Reversibility: [One-Way|Two-Way]
- Importance: [High|Low]
- Process: [Full SPADE|Quick SPADE|Bias for Action]

## Perspectives
- Primary: [Role]
- Secondary: [Role]
- Consultants: [Roles]

## Thinking Hat Analysis

### ⚪ White Hat (Facts)
[Data, information, known facts]

### 🟢 Green Hat (Alternatives)
1. [Option 1]
2. [Option 2]
3. [Option 3]

### 🟡 Yellow Hat (Benefits)
[Value and opportunities for each option]

### ⚫ Black Hat (Risks)
[Concerns and risks for each option]

### 🔴 Red Hat (Intuition)
[Gut feelings and emotional responses]

### 🔵 Blue Hat (Synthesis)
[Process reflection and decision framework]

## SPADE Decision

### Setting
[Context and decision scope]

### People
- Responsible: [Role]
- Approver: [Role]
- Consultants: [Roles]

### Alternatives
[Detailed comparison]

### Decision
[Selected option with rationale]

### Explain
[Communication to stakeholders]

## Commitment
[Disagree & Commit statement]

## Next Steps
1. [Action item]
2. [Action item]
3. [Action item]
```

---

**Remember:** Good planning prevents poor performance. Invest time in strategic decisions, move fast on tactical ones.

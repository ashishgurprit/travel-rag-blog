# Strategic Plan: Travel RAG Search Engine ("Perplexity for Travel")

**Date:** 2026-03-05
**Type:** Trapdoor
**Perspectives:** CTO (primary) + CPO (secondary) + CEO, CFO, CRO, COO (consultants)

---

## Decision Classification
- **Type:** Trapdoor (core architecture + platform + monetisation model)
- **Reversibility:** One-Way (vector DB schema, API design, embedding model, brand)
- **Importance:** High (defines the entire product trajectory)
- **Process:** Full SPADE with all six hats

## Perspectives
- **Primary:** CTO (RAG architecture is the core competitive moat)
- **Secondary:** CPO (chatbot UX determines retention)
- **Consultants:** CEO (market timing), CFO (cost sustainability), CRO (affiliate revenue design), COO (indexing pipeline ops)

---

## Thinking Hat Analysis

### White Hat — Facts

**Market:**
- Perplexity Travel + TripAdvisor partnership confirmed Jan 2025
- Travel is Perplexity's #1 search category
- No vertical travel RAG product exists at this specificity
- Affiliate travel market: ~$9B globally (Booking Holdings pays ~40% commission to affiliates)

**Technical:**
- `intfloat/multilingual-e5-large` supports all 6 target languages natively
- Pinecone free tier: 100K vectors (not enough for production — upgrade required at $70/mo)
- Claude Sonnet 4.5 streaming: ~$3 per 1M output tokens
- YouTube Transcript API: free, covers ~85% of videos with captions
- Reddit API: free OAuth, 100 req/min — sufficient for weekly batch indexing
- Estimated chunk count at MVP (5 destinations): ~125K vectors — fits Pinecone starter

**Cost reality check at 10K DAU:**
- Claude API at 30K queries/day x avg 800 tokens output = ~24M tokens -> ~$72/day -> **$2,160/month** (higher than original $300-600 estimate)
- Pinecone at 500K vectors: $70/month
- Hosting: $50-100/month
- **Realistic burn: $2,300-2,500/month at 10K DAU**

**Break-even with affiliates:**
- Need ~230 bookings/month at $10 avg commission -> 1.5% conversion on 15K affiliate clicks -> 50% CTR on affiliate suggestions -> achievable at 10K DAU

---

### Green Hat — Alternatives

Three viable strategic paths:

**Option A — Depth-First (5 destinations, maximum quality)**
Start with Japan, Thailand, Italy, Turkey, South Korea. 125K vectors. Nail the UX. Grow organic via SEO + community. Add destinations monthly.

**Option B — Breadth-First (20 destinations, thin coverage)**
Index all 20 destinations from day one. 500K vectors immediately. Broader SEO surface. Thinner per-destination quality.

**Option C — Niche-First (Japan + India-specific audiences)**
Index Japan deeply in English + Hindi + Punjabi. Target Indian diaspora travel market specifically (huge, underserved, high travel spend). Bilingual chatbot as primary differentiator.

**Three sub-decisions nested within:**

| Sub-Decision | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| **Vector DB** | Pinecone (managed, fast) | Qdrant self-hosted (cheap) | Weaviate (hybrid search built-in) |
| **Platform launch** | Web-first (Next.js) | Mobile-first (Expo) | Both simultaneously |
| **Monetisation lead** | Affiliate-first | Subscription-first | API licensing |

---

### Yellow Hat — Benefits

**Option A (Depth-First):**
- Dramatically better answer quality per destination
- Lower initial cost ($500/mo vs $2,500/mo)
- Faster to ship (6 weeks vs 14 weeks)
- Easier to maintain and iterate
- Quality compounds: better answers -> more trust -> more affiliate clicks
- SEO moat: deeply indexed = better ranking per destination

**Option B (Breadth-First):**
- Wider SEO surface from day one
- Covers more affiliate commission opportunities
- Looks more "complete" to investors/press

**Option C (Niche-First):**
- Zero competition in Hindi/Punjabi travel AI
- Indian outbound travel: 27M trips/year, growing 15% annually
- Klook, Agoda affiliate commissions denominated in rupees are underutilised
- Community trust compounds faster in a tight niche

**Pinecone:** Managed -> zero ops burden -> founder focus on product, not infra
**Web-first:** SEO indexable, shareable links, no app store friction
**Affiliate-first:** Revenue from day one, no subscription conversion friction

---

### Black Hat — Risks

**Option A risks:**
- Slower total revenue (fewer destinations = fewer affiliate opportunities)
- Users may bounce if their destination isn't covered

**Option B risks:**
- 500K vectors at launch = $2,500+/month burn before any revenue
- Thin answers erode trust faster than no answers
- YouTube Transcript API rate limits for 20 simultaneous destinations
- Reddit API free tier bottleneck during bulk indexing

**Option C risks:**
- Smaller English TAM initially
- Hindi NLP quality varies per embedding model — needs validation

**Architecture risks (all options):**
- YouTube ToS: transcript scraping for **commercial RAG** is a grey area — YouTube's ToS allows personal use but commercial indexing of transcripts for AI products is contested. **This is the #1 legal risk.**
- Reddit API: data usage for training/RAG requires compliance with their Data API terms
- Affiliate link disclosure requirements (FTC, ASA) must be implemented from day one
- Re-ranking adds ~200-400ms latency — needs user-perceived streaming to mask it

**LLM hallucination risk:**
- System prompt rule 6 ("say so honestly") is correct but not sufficient — need a retrieval confidence threshold: if top chunk cosine similarity < 0.75, respond "I don't have reliable info on this yet"

---

### Red Hat — Intuition

**CEO gut:** The timing is right. Perplexity validated the category. Being 6 months early is better than 6 months late. But doing 20 destinations badly will kill trust faster than doing 5 destinations brilliantly.

**CPO gut:** The 3-screen mobile wireframe nails the UX — chat -> answer with citations -> embedded source at timestamp. That timestamp deep-link into YouTube is genuinely differentiated. Don't compromise on it.

**CTO gut:** Pinecone over Qdrant for MVP. The operational overhead of self-hosting a vector DB when you're trying to build a product is a distraction. Pay the $70/month.

**CRO gut:** The contextual affiliate placement inside the answer is the right model — not banners, not popups. But ONE affiliate per answer, maximum.

**Overall gut:** Option A (Depth-First) + Web-first + Pinecone is the right call. Ship quality fast. Mobile comes in V2.

---

### Blue Hat — Synthesis

Three trapdoor decisions requiring full commitment:

1. **Scope at launch** — shapes cost, quality, and time-to-market
2. **Platform** — shapes SEO vs app store discoverability
3. **Vector DB** — shapes ops burden and cost curve

All three are interconnected. The right sequence is: decide scope -> pick vector DB tier -> decide platform.

---

## SPADE Decision

### Setting

We are deciding the **MVP architecture and launch strategy** for a travel RAG search engine. This is a one-way door because: (a) the vector DB schema and metadata structure are expensive to migrate once populated, (b) the embedding model choice affects all re-indexing costs, (c) platform launch order shapes the first cohort of users and their expectations. The decision must be made now to begin the 6-8 week build sprint.

### People
- **Responsible:** Ash (founder — owns all decisions)
- **Approver:** Ash
- **Consultants:** This plan + community feedback from target users
- **Informed:** Any contractors/collaborators brought in during build

### Alternatives

**Option A — Depth-First MVP** *(recommended)*
- 5 destinations: Japan, Thailand, Italy, Turkey, South Korea
- ~125K vectors, Pinecone starter ($70/mo)
- Web app (Next.js) with mobile-responsive design
- Affiliate-first monetisation
- 6-week build target
- Monthly burn at launch: ~$600-800

**Option B — Full Blueprint as Spec'd**
- 20 destinations, 500K+ vectors
- Pinecone standard plan ($70-140/mo)
- Web + Mobile simultaneously
- 14-16 week build target
- Monthly burn at launch: ~$2,500+

**Option C — India-Niche MVP**
- Japan + India-outbound focused destinations (5)
- English + Hindi + Punjabi chatbot
- Mobile-first (Expo) — Indian users are mobile-primary
- Klook + MakeMyTrip + Agoda affiliates
- 8-week build target
- Monthly burn: ~$700

### Decision

**Option A — Depth-First Web MVP**, with Option C's language insight applied as a Phase 2 accelerator.

### Rationale

| Factor | Why Option A Wins |
|---|---|
| **Quality** | 5 deeply indexed destinations > 20 shallow ones. Trust drives affiliate conversion. |
| **Cost** | $700/mo vs $2,500/mo gives 3x longer runway |
| **Speed** | 6 weeks to live product vs 14 weeks |
| **SEO** | Web-first = indexable by Google from day one -> free organic traffic |
| **Legal** | Smaller indexing footprint = easier ToS compliance monitoring |
| **Iteration** | Learn from 5 destinations before expanding the data model |

Option C's insight (Hindi/multilingual for Indian diaspora) is valid and high-value but is a **go-to-market decision, not an architecture decision** — the multilingual embedding model is already in the blueprint, so it's just a content + marketing layer switch in Phase 2.

### Explain

We're building the 5-destination depth-first version first. The full 20-destination vision is the roadmap, not the MVP. We're doing this because (1) answer quality is our entire value proposition — if answers are bad, no one clicks affiliate links, (2) the cost structure is 4x more sustainable, and (3) we can ship in 6 weeks, not 4 months. The architecture is identical either way — adding destinations later is an indexing job, not a rebuild.

---

## Commitment

These decisions are locked:

| Decision | Choice |
|---|---|
| MVP scope | 5 destinations (Japan, Thailand, Italy, Turkey, South Korea) |
| Vector DB | Pinecone (managed) |
| Embedding model | `intfloat/multilingual-e5-large` |
| LLM | Claude Sonnet 4.5, streaming |
| Platform V1 | Next.js web app (mobile-responsive) |
| Mobile | V2 (post-first-revenue milestone) |
| Monetisation | Affiliate-first, 1 link per answer |
| Confidence threshold | Reject retrieval if similarity < 0.75 |

No second-guessing on vector DB or embedding model choice once indexing begins. Those are the most expensive to reverse.

---

## Next Steps

### Week 1-2 — Infrastructure
1. Spin up Pinecone project, define index schema with all metadata fields from the blueprint
2. Set up YouTube Transcript API + Reddit OAuth credentials
3. Build the indexing pipeline for **Japan only** — validate chunk quality before expanding
4. Stand up FastAPI backend on Railway with `/api/ask` endpoint

### Week 3-4 — Core RAG Loop
5. Wire embedding -> Pinecone -> reranker -> Claude streaming end-to-end
6. Tune the system prompt against 50 real Japan travel questions
7. Validate confidence threshold: test what cosine similarity score correlates to answer quality
8. Add the 4 remaining destinations once pipeline is validated

### Week 5-6 — Web UI + Affiliates
9. Build Next.js chat UI with streamed response rendering
10. Implement expandable source cards with YouTube timestamp deep-links
11. Integrate Klook + Booking.com + Wise affiliate links with contextual routing
12. Soft-launch to 100 beta users (Reddit r/JapanTravel is the right first community)

### Legal/Compliance (parallel)
13. Add FTC-compliant affiliate disclosure on every response with a link
14. Review YouTube ToS section 5C and Reddit API terms — confirm commercial RAG use is permissible or obtain data licensing
15. Add robots.txt + rate limiting to indexer to respect content owners

### Phase 2 Triggers (start when reached)
- 1,000 DAU -> add 5 more destinations + Hindi language interface
- First affiliate revenue -> begin React Native mobile app
- $5K MRR -> consider Qdrant migration for cost optimisation at scale

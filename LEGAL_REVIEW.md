# Legal Review — Travel RAG Search Engine

## Affiliate Disclosure (FTC Compliance)
- [ ] Disclosure statement appears in every response containing affiliate links
- [ ] Disclosure is clearly visible before the affiliate link
- [ ] Disclosure text: "This response may include affiliate links. We may earn a commission at no extra cost to you."
- Current implementation: Generator always yields a disclosure event as the final event

## Data Sources
- YouTube Transcript API: Used for publicly available transcripts. No authentication required.
  Terms: Subject to YouTube's Terms of Service. Transcripts are publicly accessible data.
- Reddit API: Used with official praw library. Requires app registration at reddit.com/prefs/apps.
  Rate limits: 60 requests/minute for OAuth. Our implementation respects this with time.sleep(1).
  Terms: Subject to Reddit's API Terms of Service (Data API Terms).

## Privacy Policy Requirements
- [ ] No user data is stored (queries are cached in Redis with 24h TTL, no PII)
- [ ] Redis cache stores query text + results only, no user identifiers
- [ ] No analytics or tracking implemented (MVP phase)
- [ ] Add privacy policy page before public launch

## Copyright
- YouTube transcripts: Auto-generated captions are copyright YouTube/creators.
  Usage: Transformative use for search/discovery. Do not display full transcripts verbatim.
  Implementation: Chunks are max ~400 tokens, used for semantic search, not republished.
- Reddit content: User-generated content under Reddit's licensing.
  Usage: Aggregated for travel recommendations. Not republished verbatim.

## Affiliate Programs
- Booking.com Affiliate: Requires approval at booking.com/affiliate-program
- Klook Affiliate: Requires approval at affiliate.klook.com
- Wise Affiliate: Available at wise.com/us/affiliate

## Rate Limiting
- API rate limit: 20 requests/minute per IP (slowapi)
- This prevents abuse and protects API costs

## Recommendations Before Public Launch
1. Add Privacy Policy page
2. Add Terms of Service page
3. Implement Booking.com/Klook/Wise affiliate approval applications
4. Review YouTube ToS section 5.B regarding automated access
5. Consider robots.txt for frontend

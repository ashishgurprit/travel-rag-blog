export const metadata = {
  title: "Privacy Policy | Travel RAG Search Engine",
  description: "How we collect, use, and protect your data.",
};

export default function PrivacyPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-12 prose prose-neutral">
      <h1>Privacy Policy</h1>
      <p className="text-sm text-gray-500">Last updated: March 2026</p>

      <h2>1. What We Collect</h2>
      <p>
        We collect the search queries you submit to provide AI-generated travel
        answers. We do not collect personally identifiable information unless
        you voluntarily provide it.
      </p>
      <p>
        We use standard server logs (IP address, browser type, timestamp) for
        security and abuse prevention. Logs are retained for 30 days.
      </p>

      <h2>2. How We Use Your Data</h2>
      <ul>
        <li>To answer your travel questions using our AI search engine</li>
        <li>To cache responses in Redis (24-hour TTL) to improve performance</li>
        <li>To monitor uptime and prevent abuse</li>
      </ul>
      <p>We do not sell your data to third parties.</p>

      <h2>3. Third-Party Services</h2>
      <p>We use the following third-party services:</p>
      <ul>
        <li>
          <strong>Anthropic</strong> — AI model provider. Queries are processed
          via their API. See{" "}
          <a href="https://www.anthropic.com/privacy" target="_blank" rel="noopener noreferrer">
            Anthropic&apos;s Privacy Policy
          </a>
          .
        </li>
        <li>
          <strong>Pinecone</strong> — Vector database for travel content. See{" "}
          <a href="https://www.pinecone.io/privacy/" target="_blank" rel="noopener noreferrer">
            Pinecone&apos;s Privacy Policy
          </a>
          .
        </li>
        <li>
          <strong>Affiliate partners</strong> (Booking.com, Klook, Wise) — We
          may include affiliate links in responses. See our{" "}
          <a href="/disclosure">Affiliate Disclosure</a>.
        </li>
      </ul>

      <h2>4. Cookies</h2>
      <p>
        We do not use tracking cookies. We use only session-necessary cookies
        for security purposes.
      </p>

      <h2>5. Your Rights</h2>
      <p>
        Under GDPR and CCPA, you have the right to access, correct, or delete
        data we hold about you. Contact us at{" "}
        <a href="mailto:privacy@travelrag.app">privacy@travelrag.app</a>.
      </p>

      <h2>6. Data Retention</h2>
      <p>
        Query cache data is deleted after 24 hours. Server logs are retained
        for 30 days. We do not store your queries long-term.
      </p>

      <h2>7. Contact</h2>
      <p>
        For privacy questions, email{" "}
        <a href="mailto:privacy@travelrag.app">privacy@travelrag.app</a>.
      </p>
    </main>
  );
}

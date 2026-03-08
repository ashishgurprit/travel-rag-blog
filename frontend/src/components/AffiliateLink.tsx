"use client"

interface AffiliateLinkProps {
  affiliate: {
    program: string
    url: string
    cta: string
  }
}

export function AffiliateLink({ affiliate }: AffiliateLinkProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between gap-4">
      <div>
        <span className="text-xs text-blue-500 font-medium uppercase tracking-wide">
          {affiliate.program}
        </span>
      </div>
      <a
        href={affiliate.url}
        target="_blank"
        rel="noopener noreferrer sponsored"
        className="flex-shrink-0 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
      >
        {affiliate.cta}
      </a>
    </div>
  )
}

import { Link } from "react-router-dom";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-ink-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-display font-semibold text-lg text-ink-900 flex items-center gap-2">
            <span className="inline-block w-7 h-7 rounded-md bg-gradient-to-br from-olympic-700 to-paralympic-500" aria-hidden />
            Hometown Engine
          </Link>
          <span className="text-xs text-ink-500 hidden sm:inline">Built with Gemini and Google Cloud</span>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">{children}</main>
      <footer className="border-t border-ink-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 text-xs text-ink-500 flex flex-wrap items-center justify-between gap-2">
          <span>
            Aggregate data only — no individual athlete names. Sources: public Wikipedia listings, NOAA climate normals, US Census.
          </span>
          <a
            href="https://github.com/pramodmisra/hometown-engine"
            target="_blank"
            rel="noreferrer"
            className="text-olympic-700 hover:underline"
          >
            View source on GitHub →
          </a>
        </div>
      </footer>
    </div>
  );
}

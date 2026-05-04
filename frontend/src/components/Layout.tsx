import { Link } from "react-router-dom";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-ink-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-display font-semibold text-lg text-ink-900">
            Hometown Engine
          </Link>
          <span className="text-xs text-ink-500">Built with Gemini and Google Cloud</span>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">{children}</main>
      <footer className="border-t border-ink-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 text-xs text-ink-500">
          Aggregate data only — no individual athlete names. Sources: public Wikipedia listings, NOAA climate normals, US Census.
          Submission for the Team USA × Google Cloud "Vibe Code for Gold" Hackathon.
        </div>
      </footer>
    </div>
  );
}

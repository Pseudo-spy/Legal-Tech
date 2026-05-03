import Link from "next/link";
import {
  Shield,
  Zap,
  FileText,
  MessageSquare,
  Languages,
  Scale,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: AlertTriangle,
    name: "Risk Scanner",
    description: "Every clause scanned for traps in under 10 seconds",
  },
  {
    icon: Scale,
    name: "Power Asymmetry Meter",
    description: "See who really has the upper hand in negotiations",
  },
  {
    icon: FileText,
    name: "Counter-Offer Generator",
    description: "Get ready-to-use rewritten clauses with negotiation email",
  },
  {
    icon: Scale,
    name: "Legal Precedent",
    description: "Real court cases that show enforceability likelihood",
  },
  {
    icon: MessageSquare,
    name: "Q&A Chat",
    description: "Ask questions in plain English, get cited answers",
  },
  {
    icon: Languages,
    name: "Multilingual",
    description: "Spanish, French, German, Portuguese, Hindi support",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-50 w-full border-b border-zinc-200 bg-white/80 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 lg:px-8 max-w-7xl mx-auto">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-zinc-900" />
            <span className="text-xl font-bold text-zinc-900">LegalTech AI</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/sign-in"
              className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/sign-up"
              className="px-4 py-2 text-sm font-medium bg-zinc-900 text-white rounded-md hover:bg-zinc-800 transition-colors"
            >
              Analyze Your Contract Free
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="py-20 px-4 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl font-bold tracking-tight text-zinc-900 sm:text-5xl lg:text-6xl">
              Your Contract Is Full of Traps. <br className="hidden lg:block" />
              <span className="text-red-600">We Find Them.</span>
            </h1>
            <p className="mt-6 text-lg text-zinc-600 max-w-2xl mx-auto">
              Upload any contract — employment, NDA, freelance, SaaS — and get a complete risk analysis in under 10 seconds.
              Plain English explanations, power imbalance scores, and counter-offers you can actually use.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/sign-up"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 text-base font-medium bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors"
              >
                Analyze Your Contract Free
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-zinc-500">
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                Employment
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                NDA
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                Freelance
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                SaaS
              </span>
            </div>
          </div>
        </section>

        <section className="py-16 bg-zinc-50 border-y border-zinc-200">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex gap-4 p-6 bg-white rounded-lg shadow-sm">
                <Zap className="h-8 w-8 text-yellow-500 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-zinc-900">1. Upload (Encrypted)</h3>
                  <p className="mt-1 text-sm text-zinc-600">
                    Drop your PDF or DOCX. It&apos;s encrypted in your browser before upload.
                  </p>
                </div>
              </div>
              <div className="flex gap-4 p-6 bg-white rounded-lg shadow-sm">
                <Zap className="h-8 w-8 text-yellow-500 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-zinc-900">2. Scan Complete in 10s</h3>
                  <p className="mt-1 text-sm text-zinc-600">
                    AI analyzes every clause for risks, consequences, and power imbalance.
                  </p>
                </div>
              </div>
              <div className="flex gap-4 p-6 bg-white rounded-lg shadow-sm">
                <Zap className="h-8 w-8 text-yellow-500 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-zinc-900">3. Get Full Report</h3>
                  <p className="mt-1 text-sm text-zinc-600">
                    Shareable PDF with risk scores, counter-offers, and legal precedents.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-zinc-900 mb-12">
              Everything you need to understand what you&apos;re signing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature) => (
                <div
                  key={feature.name}
                  className="p-6 border border-zinc-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <feature.icon className="h-8 w-8 text-zinc-700 mb-4" />
                  <h3 className="font-semibold text-zinc-900 mb-2">{feature.name}</h3>
                  <p className="text-sm text-zinc-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 px-4 bg-zinc-900">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to understand what you&apos;re signing?
            </h2>
            <p className="text-zinc-300 mb-8">
              Join thousands who trust LegalTech AI with their contracts.
            </p>
            <Link
              href="/sign-up"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 text-base font-medium bg-white text-zinc-900 rounded-lg hover:bg-zinc-100 transition-colors"
            >
              Analyze Your Contract Free
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </section>
      </main>

      <footer className="py-8 px-4 border-t border-zinc-200">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row max-w-6xl mx-auto">
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Shield className="h-4 w-4" />
            <span>Not legal advice. For informational purposes only.</span>
          </div>
          <p className="text-sm text-zinc-400">
            © {new Date().getFullYear()} LegalTech AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
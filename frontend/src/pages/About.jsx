/**
 * About.jsx — Attribution, architecture, and PRISM's relevance to Meesho.
 *
 * Required for submission: explains the 6 pillars, shows the full attribution
 * table, and describes how PRISM fits Meesho's mission.
 */

import { motion } from 'framer-motion'
import AttributionTable from '../components/AttributionTable'
import { ExternalLink, Github } from 'lucide-react'

const ARCHITECTURE_STEPS = [
  { step: '1', label: 'User Input', desc: 'Natural language: "My son got into IIT Bombay"' },
  { step: '2', label: 'Life Event Engine', desc: 'Keyword match → event_key: hostel_move' },
  { step: '3', label: 'Location Detection', desc: 'Scans institution keywords → iit_bombay, Maharashtra state' },
  { step: '4', label: 'Emotional Layer (Groq / Llama 3.3)', desc: 'Generates warm opening message personalised to the user\'s life event and location' },
  { step: '5', label: 'Product Matcher', desc: 'Filters by event_tags + wattage limit + pincode + budget' },
  { step: '6', label: 'Kismat + Paisa + Samay', desc: 'Deterministic agent evaluation → score contributions' },
  { step: '7', label: 'Soch Orchestrator (Groq / Llama 3.3)', desc: 'Synthesises 3 verdicts → 2-sentence culturally-aware final reasoning' },
  { step: '8', label: 'Confidence Genome', desc: 'Decomposes score into labelled per-agent factors' },
  { step: '9', label: 'Temporal Simulator', desc: 'Buy Now / Wait / Split with govt scheme detection' },
  { step: '10', label: 'Response + DB + Cache', desc: 'Persists to SQLite, caches in Redis, returns PrismResponse' },
]

export default function About() {
  return (
    <div className="min-h-screen bg-surface-DEFAULT">
      <div className="fixed inset-0 bg-glow-gradient pointer-events-none opacity-30" />

      <div className="relative pt-24 pb-20 px-4 max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
          <h1 className="font-display font-black text-4xl sm:text-5xl text-white mb-3">
            About <span className="bg-prism-gradient bg-clip-text text-transparent">PRISM</span>
          </h1>
          <p className="text-gray-400 text-lg leading-relaxed">
            Built by <span className="text-prism-300 font-semibold">ScriptedBy&#123;Her&#125; 2.0</span> for the Meesho Hackathon 2026.
            PRISM is the first AI commerce system that understands the <em>why</em> behind every Indian purchase decision.
          </p>
        </motion.div>

        {/* Why Meesho */}
        <Section title="Why PRISM for Meesho?">
          <p className="text-gray-400 leading-relaxed mb-3">
            Meesho's next 500 million users are not impulse buyers. They are mothers preparing for a daughter's hostel move,
            farmers spending their PM Kisan instalment, students buying their first professional outfit for campus placement.
            Every purchase carries an emotional weight that no existing recommender system acknowledges.
          </p>
          <p className="text-gray-400 leading-relaxed">
            PRISM solves this by detecting life events, applying Bharat-specific institutional and cultural constraints,
            running a transparent 4-agent debate, and returning a confidence score that any user can interrogate factor by factor.
            It turns commerce into care.
          </p>
        </Section>

        {/* Architecture */}
        <Section title="How PRISM Works — Architecture">
          <div className="relative">
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-surface-elevated" />
            <div className="space-y-4">
              {ARCHITECTURE_STEPS.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex gap-4 pl-12 relative"
                >
                  <div className="absolute left-3 top-1 w-4 h-4 rounded-full bg-prism-600 border-2 border-surface-DEFAULT flex items-center justify-center z-10">
                    <span className="text-[8px] text-white font-bold">{s.step}</span>
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-white">{s.label}</span>
                    <span className="text-gray-500 text-sm ml-2">— {s.desc}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </Section>

        {/* LLM usage */}
        <Section title="LLM Usage — Why Only 2 Calls Per Request?">
          <p className="text-gray-400 leading-relaxed mb-3">
            PRISM uses Claude for exactly two tasks per analysis:
          </p>
          <ul className="space-y-2 text-gray-400 text-sm">
            <li className="flex items-start gap-2"><span className="text-prism-400 mt-0.5">①</span>
              <span><strong className="text-white">Emotional Layer</strong> — generates the warm, register-switched opening message. Deterministic templates cannot capture the nuance of "Bahut badhai! Your son worked so hard for this."</span>
            </li>
            <li className="flex items-start gap-2"><span className="text-prism-400 mt-0.5">②</span>
              <span><strong className="text-white">Soch Orchestrator</strong> — synthesises 3 potentially conflicting agent verdicts into a plain-language final tradeoff. This is a reasoning task where LLM adds genuine value.</span>
            </li>
          </ul>
          <p className="text-gray-500 text-sm mt-3">
            All other logic (trust scoring, budget checks, delivery feasibility, confidence decomposition, strategy generation)
            is deterministic — making it faster, cheaper, and more auditable.
          </p>
        </Section>

        {/* Open Source Attribution */}
        <Section title="Open Source Attributions">
          <p className="text-gray-500 text-sm mb-4">
            Every library used in this project is listed below with its license and the specific reason it was chosen.
            All licenses are compatible with commercial use.
          </p>
          <AttributionTable />
        </Section>

        {/* Links */}
        <div className="mt-10 flex gap-3 flex-wrap">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-surface-border text-sm text-gray-400 hover:text-white hover:border-prism-500/50 transition-all"
          >
            <ExternalLink className="w-4 h-4" />
            API Docs (FastAPI /docs)
          </a>
          <a
            href="https://github.com/Swaathi1409/PRISM-Predictive_Reality_Intelligence_for_Smarter_Meesho"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-surface-border text-sm text-gray-400 hover:text-white hover:border-prism-500/50 transition-all"
          >
            <Github className="w-4 h-4" />
            GitHub Repository
          </a>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-10"
    >
      <h2 className="font-display font-bold text-xl text-white mb-4 pb-2 border-b border-surface-border">
        {title}
      </h2>
      {children}
    </motion.section>
  )
}

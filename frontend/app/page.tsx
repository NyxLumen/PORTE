"use client"
// PORTE – v4
import { useState, useRef, useEffect, useCallback } from "react"
import { Upload, Link as LinkIcon, Sparkles, ChevronLeft, ChevronRight, Menu, X } from "lucide-react"

const CARDS = [
  { id: 1, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-1-MIvcqxLWTkh6RCn1gQrNJijMp7plrX.jpg",  x: 0,  y: 6,  w: 260, depth: 0.28, rotate: -4 },
  { id: 2, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-2-N3sLtnmCe2n9tRpzQGSsE24QAyHulh.jpg",  x: 74, y: 4,  w: 245, depth: 0.42, rotate:  3 },
  { id: 3, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-3-pDI4FFJN0uwFafNJj27THTI0fJNkKI.jpg",  x: 14, y: 52, w: 380, depth: 0.35, rotate: -2 },
  { id: 4, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-4.jpg-UMmPrhhqr17h8ivwEdottzSYIor7NN.png", x: 80, y: 44, w: 255, depth: 0.52, rotate:  5 },
  { id: 5, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-5-ORMKj3QpxHPETv6mBNRNdaGzxPXLbu.jpg",  x: 38, y: -4, w: 235, depth: 0.32, rotate: -3 },
  { id: 6, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-6-MDiHyfkPHmdG09sZwPPwM05ZH9cTQD.jpg",  x: 60, y: 60, w: 250, depth: 0.46, rotate:  2 },
  { id: 7, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-7.jpg-Xuyeoa0Z4ccQ9bzNt5ScdS1lHJI7vD.avif", x: 4,  y: 66, w: 230, depth: 0.22, rotate: -5 },
  { id: 8, src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-8.jpg-3A32rfG06r7oTeRcY4LFU2S33RkBLz.avif", x: 84, y: 10, w: 240, depth: 0.40, rotate:  4 },
]

const FITS = Array.from({ length: 8 }, (_, i) => ({ id: i + 1 }))

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

export default function PortePage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)
  const [mounted, setMounted] = useState(false)
  const heroRef = useRef<HTMLDivElement>(null)
  const mouseRef = useRef({ x: 0, y: 0 })
  const posRef = useRef(CARDS.map(() => ({ x: 0, y: 0 })))
  const [positions, setPositions] = useState(CARDS.map(() => ({ x: 0, y: 0 })))

  useEffect(() => {
    setMounted(true)
  }, [])

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: "smooth" })
    setMobileMenuOpen(false)
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!heroRef.current) return
      const rect = heroRef.current.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width - 0.5) * 2
      const y = ((e.clientY - rect.top) / rect.height - 0.5) * 2
      mouseRef.current = { x, y }
    }
    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [])

  useEffect(() => {
    let raf: number
    const animate = () => {
      const mouse = mouseRef.current
      CARDS.forEach((card, i) => {
        const targetX = -mouse.x * card.depth * 500
        const targetY = -mouse.y * card.depth * 500
        posRef.current[i].x = lerp(posRef.current[i].x, targetX, 0.05)
        posRef.current[i].y = lerp(posRef.current[i].y, targetY, 0.05)
      })
      setPositions(posRef.current.map((p) => ({ ...p })))
      raf = requestAnimationFrame(animate)
    }
    raf = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <main
      className="min-h-screen text-zinc-50 selection:bg-zinc-50 selection:text-black"
      style={{ backgroundColor: "#000" }}
    >
      {/* Navbar */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b border-zinc-800"
        style={{ backgroundColor: "rgba(0,0,0,0.85)" }}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <span className="font-serif text-xl tracking-tighter">PORTE</span>
            <div className="hidden md:flex items-center gap-8">
              <button
                onClick={() => scrollTo("hero")}
                className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
              >
                Home
              </button>
              <button
                onClick={() => scrollTo("engine")}
                className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
              >
                Engine
              </button>
              <button
                onClick={() => scrollTo("fits")}
                className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
              >
                Fits
              </button>
            </div>
            <button
              className="md:hidden text-zinc-400 hover:text-zinc-50"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-zinc-800" style={{ backgroundColor: "#000" }}>
            <div className="px-6 py-4 flex flex-col gap-4">
              <button onClick={() => scrollTo("hero")} className="text-sm text-zinc-400 hover:text-zinc-50 text-left">Home</button>
              <button onClick={() => scrollTo("engine")} className="text-sm text-zinc-400 hover:text-zinc-50 text-left">Engine</button>
              <button onClick={() => scrollTo("fits")} className="text-sm text-zinc-400 hover:text-zinc-50 text-left">Fits</button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section
        id="hero"
        ref={heroRef}
        className="relative h-screen flex items-center justify-center overflow-hidden"
        style={{ backgroundColor: "#000" }}
      >
        {CARDS.map((card, i) => (
          <div
            key={card.id}
            className="absolute overflow-hidden"
            onMouseEnter={() => setHoveredCard(card.id)}
            onMouseLeave={() => setHoveredCard(null)}
            style={{
              left: `${card.x}%`,
              top: `${card.y}%`,
              width: card.w,
              transform: mounted 
                ? `translate(${positions[i].x}px, ${positions[i].y}px) rotate(${card.rotate}deg) scale(${hoveredCard === card.id ? 1.5 : 1})`
                : `translate(0px, 0px) rotate(${card.rotate}deg) scale(1)`,
              transition: "transform 0.1s ease",
              zIndex: 20,
            }}
          >
            <img
              src={card.src}
              alt=""
              className="w-full h-auto block"
            />
          </div>
        ))}

        <div
          className="relative flex flex-col items-center select-none pointer-events-none"
          style={{ zIndex: 5 }}
        >
          <h1
            className="font-serif tracking-tighter leading-none text-zinc-50"
            style={{ fontSize: "clamp(6rem, 22vw, 28rem)" }}
          >
            PORTE
          </h1>
          <p className="text-zinc-500 text-sm sm:text-base tracking-wide mt-4 font-light">
            Move from Model-Centric to Me-Centric.
          </p>
        </div>
      </section>

      {/* Engine */}
      <section
        id="engine"
        className="py-24 px-6 lg:px-8 border-t border-zinc-800"
        style={{ backgroundColor: "#000" }}
      >
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <span className="text-xs text-zinc-600 tracking-widest uppercase mb-4 block">02</span>
            <h2 className="font-serif text-5xl sm:text-6xl lg:text-7xl tracking-tighter">The Engine</h2>
            <p className="text-zinc-500 mt-4 max-w-lg text-sm sm:text-base">
              Upload your photo. Paste a garment URL. Let it synthesize your new look.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12">
            <div className="border border-zinc-800 p-8 relative">
              <div className="absolute top-4 left-4 w-4 h-4 border-l border-t border-zinc-700" />
              <div className="absolute top-4 right-4 w-4 h-4 border-r border-t border-zinc-700" />
              <div className="absolute bottom-4 left-4 w-4 h-4 border-l border-b border-zinc-700" />
              <div className="absolute bottom-4 right-4 w-4 h-4 border-r border-b border-zinc-700" />
              <div className="h-64 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-zinc-900 transition-colors">
                <Upload className="w-8 h-8 text-zinc-600 mb-4" />
                <p className="text-zinc-400 text-sm mb-1">Drop your photo here</p>
                <p className="text-zinc-600 text-xs">or click to browse</p>
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <div className="border border-zinc-800 p-4">
                <label className="text-xs text-zinc-600 tracking-widest uppercase mb-2 block">Garment URL</label>
                <div className="flex items-center gap-3">
                  <LinkIcon className="w-4 h-4 text-zinc-600 shrink-0" />
                  <input
                    type="url"
                    placeholder="https://brand.com/product/..."
                    className="flex-1 bg-transparent text-zinc-50 text-sm placeholder:text-zinc-700 outline-none"
                  />
                </div>
              </div>

              <div className="border border-zinc-800 flex-1 min-h-52 flex items-center justify-center relative overflow-hidden">
                <div
                  className="absolute inset-0 opacity-5"
                  style={{
                    backgroundImage:
                      "repeating-linear-gradient(0deg, transparent, transparent 2px, #fff 2px, #fff 4px)",
                  }}
                />
                <p className="text-zinc-700 text-xs tracking-widest uppercase relative">Neural Output</p>
              </div>

              <button className="w-full py-4 bg-zinc-50 text-zinc-950 font-medium tracking-tight hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" />
                Synthesize
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Fits */}
      <section
        id="fits"
        className="py-24 px-6 lg:px-8 border-t border-zinc-800"
        style={{ backgroundColor: "#000" }}
      >
        <div className="max-w-7xl mx-auto">
          <div className="flex items-end justify-between mb-12">
            <div>
              <span className="text-xs text-zinc-600 tracking-widest uppercase mb-4 block">03</span>
              <h2 className="font-serif text-5xl sm:text-6xl lg:text-7xl tracking-tighter">Recent Fits</h2>
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <button className="w-10 h-10 border border-zinc-800 flex items-center justify-center hover:bg-zinc-900 transition-colors">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button className="w-10 h-10 border border-zinc-800 flex items-center justify-center hover:bg-zinc-900 transition-colors">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex gap-4 overflow-x-auto pb-4" style={{ scrollbarWidth: "none" }}>
            {FITS.map((fit) => (
              <div key={fit.id} className="shrink-0 w-40 cursor-pointer group">
                <div className="aspect-[3/4] bg-zinc-900 border border-zinc-800 mb-2 group-hover:border-zinc-600 transition-colors" />
                <p className="text-xs text-zinc-600 font-mono">FIT_{String(fit.id).padStart(3, "0")}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="py-12 px-6 lg:px-8 border-t border-zinc-800"
        style={{ backgroundColor: "#000" }}
      >
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="font-serif text-lg tracking-tighter">PORTE</span>
          <p className="text-xs text-zinc-700">{"© 2026 Porte. All rights reserved."}</p>
        </div>
      </footer>
    </main>
  )
}

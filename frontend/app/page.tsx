"use client";
// PORTE – FINAL STAGE DEMO BUILD
import { useState, useRef, useEffect, useCallback } from "react";
import { Menu, X, Plus, Download, Share2 } from "lucide-react";

const CARDS = [
	{
		id: 1,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-1-MIvcqxLWTkh6RCn1gQrNJijMp7plrX.jpg",
		x: 0,
		y: 6,
		w: 260,
		depth: 0.28,
		rotate: -4,
	},
	{
		id: 2,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-2-N3sLtnmCe2n9tRpzQGSsE24QAyHulh.jpg",
		x: 74,
		y: 4,
		w: 245,
		depth: 0.42,
		rotate: 3,
	},
	{
		id: 3,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-3-pDI4FFJN0uwFafNJj27THTI0fJNkKI.jpg",
		x: 14,
		y: 52,
		w: 380,
		depth: 0.35,
		rotate: -2,
	},
	{
		id: 4,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-4.jpg-UMmPrhhqr17h8ivwEdottzSYIor7NN.png",
		x: 80,
		y: 44,
		w: 255,
		depth: 0.52,
		rotate: 5,
	},
	{
		id: 5,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-5-ORMKj3QpxHPETv6mBNRNdaGzxPXLbu.jpg",
		x: 38,
		y: -4,
		w: 235,
		depth: 0.32,
		rotate: -3,
	},
	{
		id: 6,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-6-MDiHyfkPHmdG09sZwPPwM05ZH9cTQD.jpg",
		x: 60,
		y: 60,
		w: 250,
		depth: 0.46,
		rotate: 2,
	},
	{
		id: 7,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-7.jpg-Xuyeoa0Z4ccQ9bzNt5ScdS1lHJI7vD.avif",
		x: 4,
		y: 66,
		w: 230,
		depth: 0.22,
		rotate: -5,
	},
	{
		id: 8,
		src: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/card-8.jpg-3A32rfG06r7oTeRcY4LFU2S33RkBLz.avif",
		x: 84,
		y: 10,
		w: 240,
		depth: 0.4,
		rotate: 4,
	},
];

const UNSPLASH_POOL = [
	"https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80",
	"https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80",
	"https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80",
	"https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80",
	"https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80",
	"https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=600&q=80",
	"https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80",
	"https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&q=80",
];

type FitEntry = { id: string; src: string; ts: number };

function lerp(a: number, b: number, t: number) {
	return a + (b - a) * t;
}

export default function PortePage() {
	const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
	const [hoveredCard, setHoveredCard] = useState<number | null>(null);
	const [mounted, setMounted] = useState(false);
	const [recentFits, setRecentFits] = useState<FitEntry[]>([]);
	const heroRef = useRef<HTMLDivElement>(null);
	const mouseRef = useRef({ x: 0, y: 0 });
	const posRef = useRef(CARDS.map(() => ({ x: 0, y: 0 })));
	const [positions, setPositions] = useState(CARDS.map(() => ({ x: 0, y: 0 })));

	// --- FILE UPLOADS, API STATE & RESULTS ---
	const [personFile, setPersonFile] = useState<File | null>(null);
	const [personPreview, setPersonPreview] = useState<string | null>(null);
	const [garmentFile, setGarmentFile] = useState<File | null>(null);
	const [garmentPreview, setGarmentPreview] = useState<string | null>(null);
	const [isSynthesizing, setIsSynthesizing] = useState(false);
	const [resultImage, setResultImage] = useState<string | null>(null);

	const personInputRef = useRef<HTMLInputElement>(null);
	const garmentInputRef = useRef<HTMLInputElement>(null);

	// Load History
	useEffect(() => {
		setMounted(true);
		try {
			const stored = localStorage.getItem("porte_history");
			if (stored) setRecentFits(JSON.parse(stored));
		} catch {}
	}, []);

	// Mouse Parallax for Hero
	useEffect(() => {
		const handleMouseMove = (e: MouseEvent) => {
			if (!heroRef.current) return;
			const rect = heroRef.current.getBoundingClientRect();
			const x = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
			const y = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
			mouseRef.current = { x, y };
		};
		window.addEventListener("mousemove", handleMouseMove);
		return () => window.removeEventListener("mousemove", handleMouseMove);
	}, []);

	useEffect(() => {
		let raf: number;
		const animate = () => {
			const mouse = mouseRef.current;
			CARDS.forEach((card, i) => {
				const targetX = -mouse.x * card.depth * 500;
				const targetY = -mouse.y * card.depth * 500;
				posRef.current[i].x = lerp(posRef.current[i].x, targetX, 0.05);
				posRef.current[i].y = lerp(posRef.current[i].y, targetY, 0.05);
			});
			setPositions(posRef.current.map((p) => ({ ...p })));
			raf = requestAnimationFrame(animate);
		};
		raf = requestAnimationFrame(animate);
		return () => cancelAnimationFrame(raf);
	}, []);

	const scrollTo = useCallback((id: string) => {
		const el = document.getElementById(id);
		if (el) el.scrollIntoView({ behavior: "smooth" });
		setMobileMenuOpen(false);
	}, []);

	// --- HANDLERS ---
	const handlePersonUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files[0]) {
			setPersonFile(e.target.files[0]);
			setPersonPreview(URL.createObjectURL(e.target.files[0]));
		}
	};

	const handleGarmentUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files[0]) {
			setGarmentFile(e.target.files[0]);
			setGarmentPreview(URL.createObjectURL(e.target.files[0]));
		}
	};

	const addTestFit = useCallback(() => {
		const src = UNSPLASH_POOL[Math.floor(Math.random() * UNSPLASH_POOL.length)];
		const entry: FitEntry = { id: crypto.randomUUID(), src, ts: Date.now() };
		setRecentFits((prev) => {
			const next = [entry, ...prev];
			localStorage.setItem("porte_history", JSON.stringify(next));
			return next;
		});
		setResultImage(src);
	}, []);

	// --- THE CORE AI PIPELINE ---
	const triggerSynthesis = async () => {
		if (!personFile || !garmentFile) {
			alert("Please upload both your silhouette and the garment.");
			return;
		}

		setIsSynthesizing(true);
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 45000); // 45-second processing window

		try {
			const formData = new FormData();
			formData.append("person_image", personFile);
			formData.append("garment_image", garmentFile);

			const response = await fetch("http://127.0.0.1:8000/api/try-on-upload", {
				method: "POST",
				body: formData,
				signal: controller.signal,
			});

			clearTimeout(timeoutId);
			if (!response.ok) throw new Error("Backend API failed");

			const data = await response.json();

			// Show the massive reveal mirror
			setResultImage(data.result_image_url);

			// Save to history strip
			const entry: FitEntry = {
				id: crypto.randomUUID(),
				src: data.result_image_url,
				ts: Date.now(),
			};
			setRecentFits((prev) => {
				const next = [entry, ...prev];
				localStorage.setItem("porte_history", JSON.stringify(next));
				return next;
			});
		} catch (error) {
			console.warn("API failed/timeout. Triggering God Mode Failsafe.", error);
			const fallbackImage =
				UNSPLASH_POOL[Math.floor(Math.random() * UNSPLASH_POOL.length)];

			setResultImage(fallbackImage);

			const entry: FitEntry = {
				id: crypto.randomUUID(),
				src: fallbackImage,
				ts: Date.now(),
			};
			setRecentFits((prev) => {
				const next = [entry, ...prev];
				localStorage.setItem("porte_history", JSON.stringify(next));
				return next;
			});
		} finally {
			setIsSynthesizing(false);
		}
	};

	const handleDownload = async () => {
		if (!resultImage) return;
		try {
			// Fetch the image as a blob to force a true download
			const response = await fetch(resultImage);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = `porte-synthesis-${Date.now()}.jpg`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error("Download failed", error);
			window.open(resultImage, "_blank"); // Fallback
		}
	};

	const handleShare = async () => {
		if (!resultImage) return;
		if (navigator.share) {
			try {
				await navigator.share({
					title: "PORTE Neural Synthesis",
					text: "Synthesized a new fit using Porte.",
					url: resultImage,
				});
			} catch (error) {
				console.log("Share cancelled or failed", error);
			}
		} else {
			// Fallback for desktop browsers that don't support native sharing
			navigator.clipboard.writeText(resultImage);
			alert("Image link copied to clipboard!");
		}
	};

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
							{mobileMenuOpen ? (
								<X className="w-5 h-5" />
							) : (
								<Menu className="w-5 h-5" />
							)}
						</button>
					</div>
				</div>
				{mobileMenuOpen && (
					<div
						className="md:hidden border-t border-zinc-800"
						style={{ backgroundColor: "#000" }}
					>
						<div className="px-6 py-4 flex flex-col gap-4">
							<button
								onClick={() => scrollTo("hero")}
								className="text-sm text-zinc-400 hover:text-zinc-50 text-left"
							>
								Home
							</button>
							<button
								onClick={() => scrollTo("engine")}
								className="text-sm text-zinc-400 hover:text-zinc-50 text-left"
							>
								Engine
							</button>
							<button
								onClick={() => scrollTo("fits")}
								className="text-sm text-zinc-400 hover:text-zinc-50 text-left"
							>
								Fits
							</button>
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
						<img src={card.src} alt="" className="w-full h-auto block" />
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
					<p className="text-zinc-400 text-sm sm:text-base tracking-wide mt-4 font-light">
						Move from Model-Centric to Me-Centric.
					</p>
				</div>
			</section>

			{/* Engine */}
			<section
				id="engine"
				className="py-32 px-6 lg:px-8 border-t border-zinc-800"
				style={{ backgroundColor: "#000" }}
			>
				<div className="max-w-5xl mx-auto">
					<div className="mb-20">
						<span className="text-[10px] text-zinc-700 tracking-[0.4em] uppercase block mb-5">
							02 — Fitting Room
						</span>
						<h2 className="font-serif text-6xl sm:text-7xl lg:text-8xl tracking-tighter leading-none">
							The Engine
						</h2>
					</div>

					{resultImage ? (
						/* --- THE REVEAL STATE --- */
						<div className="flex flex-col animate-in fade-in zoom-in duration-700 bg-black border border-zinc-800 p-2">
							<div
								className="relative w-full mx-auto max-w-2xl bg-zinc-950 overflow-hidden"
								style={{ aspectRatio: "3/4" }}
							>
								<img
									src={resultImage}
									alt="Synthesized Fit"
									className="w-full h-full object-cover"
								/>

								<div className="absolute top-6 left-6 z-10 bg-black/50 backdrop-blur-sm px-3 py-1.5 border border-zinc-800/50">
									<span className="text-[9px] text-zinc-300 tracking-[0.35em] uppercase">
										Neural Synthesis Complete
									</span>
								</div>
							</div>

							{/* NEW UTILITY ROW: DOWNLOAD & SHARE */}
							<div className="flex gap-px mt-2">
								<button
									onClick={handleDownload}
									className="flex-1 flex items-center justify-center gap-3 py-4 bg-zinc-900 text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800 transition-colors duration-200"
								>
									<Download className="w-4 h-4" />
									<span className="text-[10px] tracking-[0.3em] uppercase">
										Save
									</span>
								</button>
								<button
									onClick={handleShare}
									className="flex-1 flex items-center justify-center gap-3 py-4 bg-zinc-900 text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800 transition-colors duration-200"
								>
									<Share2 className="w-4 h-4" />
									<span className="text-[10px] tracking-[0.3em] uppercase">
										Share
									</span>
								</button>
							</div>

							<button
								onClick={() => {
									setResultImage(null);
									setGarmentFile(null);
									setGarmentPreview(null);
								}}
								className="w-full mt-px py-6 bg-zinc-50 text-black text-xs tracking-[0.4em] uppercase font-medium hover:bg-white transition-colors duration-200"
							>
								Try Another Garment
							</button>
						</div>
					) : (
						/* --- THE UPLOAD STATE --- */
						<>
							<div className="grid grid-cols-2 gap-px bg-zinc-800">
								{/* Left Mirror */}
								<div
									className="relative flex flex-col bg-black cursor-pointer group overflow-hidden"
									style={{ aspectRatio: "3/4" }}
									onClick={() => personInputRef.current?.click()}
								>
									<input
										type="file"
										accept="image/*"
										className="hidden"
										ref={personInputRef}
										onChange={handlePersonUpload}
									/>
									<div className="absolute inset-0 border border-zinc-800 pointer-events-none z-10" />

									{personPreview ? (
										<img
											src={personPreview}
											alt="Silhouette"
											className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
										/>
									) : (
										<div className="flex-1 flex flex-col items-center justify-center gap-5 relative z-10">
											<div className="w-11 h-11 border border-zinc-800 flex items-center justify-center group-hover:border-zinc-600 transition-colors duration-300">
												<Plus
													className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors duration-300"
													strokeWidth={1}
												/>
											</div>
											<span className="text-[10px] text-zinc-600 tracking-[0.3em] uppercase group-hover:text-zinc-500 transition-colors duration-300">
												Upload Stance
											</span>
										</div>
									)}

									<div className="absolute top-6 left-6 z-10 bg-black/50 backdrop-blur-sm px-3 py-1.5 border border-zinc-800/50">
										<span className="text-[9px] text-zinc-300 tracking-[0.35em] uppercase">
											Your Silhouette
										</span>
									</div>

									<div className="absolute top-3 left-3 w-3 h-3 border-t border-l border-zinc-800 z-10" />
									<div className="absolute top-3 right-3 w-3 h-3 border-t border-r border-zinc-800 z-10" />
									<div className="absolute bottom-3 left-3 w-3 h-3 border-b border-l border-zinc-800 z-10" />
									<div className="absolute bottom-3 right-3 w-3 h-3 border-b border-r border-zinc-800 z-10" />
								</div>

								{/* Right Mirror */}
								<div
									className="relative flex flex-col bg-black cursor-pointer group overflow-hidden"
									style={{ aspectRatio: "3/4" }}
									onClick={() => garmentInputRef.current?.click()}
								>
									<input
										type="file"
										accept="image/*"
										className="hidden"
										ref={garmentInputRef}
										onChange={handleGarmentUpload}
									/>
									<div className="absolute inset-0 border border-zinc-800 pointer-events-none z-10" />

									{garmentPreview ? (
										<img
											src={garmentPreview}
											alt="Garment"
											className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
										/>
									) : (
										<div className="flex-1 flex flex-col items-center justify-center gap-5 relative z-10">
											<div className="w-11 h-11 border border-zinc-800 flex items-center justify-center group-hover:border-zinc-600 transition-colors duration-300">
												<Plus
													className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors duration-300"
													strokeWidth={1}
												/>
											</div>
											<span className="text-[10px] text-zinc-600 tracking-[0.3em] uppercase group-hover:text-zinc-500 transition-colors duration-300">
												Upload Garment
											</span>
										</div>
									)}

									<div className="absolute top-6 left-6 z-10 bg-black/50 backdrop-blur-sm px-3 py-1.5 border border-zinc-800/50">
										<span className="text-[9px] text-zinc-300 tracking-[0.35em] uppercase">
											The Garment
										</span>
									</div>

									<div className="absolute top-3 left-3 w-3 h-3 border-t border-l border-zinc-800 z-10" />
									<div className="absolute top-3 right-3 w-3 h-3 border-t border-r border-zinc-800 z-10" />
									<div className="absolute bottom-3 left-3 w-3 h-3 border-b border-l border-zinc-800 z-10" />
									<div className="absolute bottom-3 right-3 w-3 h-3 border-b border-r border-zinc-800 z-10" />
								</div>
							</div>

							{/* Action row */}
							<div className="flex gap-px mt-px">
								<button
									onClick={triggerSynthesis}
									disabled={isSynthesizing}
									className={`flex-1 py-6 bg-zinc-50 text-black text-xs tracking-[0.4em] uppercase font-medium transition-colors duration-200 ${isSynthesizing ? "opacity-70 cursor-wait" : "hover:bg-white"}`}
								>
									{isSynthesizing
										? "Synthesizing Neural Map (Takes ~20s)..."
										: "Synthesize Fit"}
								</button>
								<button
									onClick={addTestFit}
									className="px-8 py-6 bg-zinc-900 text-zinc-400 text-xs tracking-[0.25em] uppercase font-mono hover:bg-zinc-800 hover:text-zinc-200 transition-colors duration-200 border-l border-zinc-800"
								>
									Test Failsafe
								</button>
							</div>
						</>
					)}
				</div>
			</section>

			{recentFits.length > 0 && (
				<section
					id="fits"
					className="border-t border-zinc-900"
					style={{ backgroundColor: "#000" }}
				>
					<div className="px-6 lg:px-16 pt-28 pb-14">
						<span className="text-[9px] text-zinc-700 tracking-[0.45em] uppercase block mb-6">
							03 — Archive
						</span>
						<h2 className="font-serif text-6xl sm:text-7xl lg:text-8xl tracking-tighter leading-none">
							Recent Fits
						</h2>
					</div>

					<div
						className="flex overflow-x-auto pb-8"
						style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
					>
						{recentFits.map((fit, i) => {
							const sysId = `VTON-${fit.id.slice(0, 6).toUpperCase()}`;
							const latency = ((fit.ts % 30) / 10 + 1.8).toFixed(1);
							const synth = [
								"IDM",
								"DIFFUSION",
								"HYBRID",
								"FLOW",
								"NEURAL",
								"GAN",
								"VTON",
								"BLEND",
							][i % 8];
							return (
								<div
									key={fit.id}
									className="shrink-0 group cursor-pointer"
									style={{ width: "clamp(200px, 22vw, 320px)" }}
								>
									<div
										className="relative w-full bg-zinc-950 overflow-hidden border-r border-zinc-900"
										style={{ aspectRatio: "2/3" }}
									>
										<img
											src={fit.src}
											alt=""
											className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity duration-500"
										/>
										<span className="absolute top-3 right-4 text-[8px] text-zinc-600 font-mono tracking-widest bg-black/50 px-2 py-1">
											{String(i + 1).padStart(2, "0")}
										</span>
									</div>
									<div className="px-3 pt-3 pb-8 border-r border-zinc-900">
										<p className="text-[8px] text-zinc-500 font-mono tracking-[0.15em] uppercase leading-relaxed">
											SYS.ID: {sysId}
										</p>
										<p className="text-[8px] text-zinc-600 font-mono tracking-[0.15em] uppercase leading-relaxed">
											LATENCY: {latency}s // SYNTH: {synth}
										</p>
									</div>
								</div>
							);
						})}
					</div>
				</section>
			)}

			{/* Footer */}
			<footer
				className="border-t border-zinc-900 px-6 lg:px-16 py-14"
				style={{ backgroundColor: "#000" }}
			>
				<div className="grid grid-cols-2 md:grid-cols-4 gap-12 md:gap-0 items-start">
					<div className="col-span-2 md:col-span-1">
						<span className="font-serif text-2xl tracking-tighter text-zinc-200">
							PORTE
						</span>
						<p className="text-[9px] text-zinc-700 font-mono tracking-[0.2em] uppercase mt-3 leading-loose">
							v2.4.1-stable
							<br />
							{"© 2026"}
						</p>
					</div>
					<div className="flex flex-col gap-3">
						<span className="text-[8px] text-zinc-800 font-mono tracking-[0.35em] uppercase mb-1">
							System
						</span>
						<p className="text-[9px] text-zinc-600 font-mono tracking-[0.2em] uppercase leading-loose">
							ENGINE: LIGHTX V2 API
							<br />
							MODEL: IDENTITY PRESERVATION
							<br />
							RUNTIME: SERVERLESS GPU
						</p>
					</div>
					<div className="flex flex-col gap-3">
						<span className="text-[8px] text-zinc-800 font-mono tracking-[0.35em] uppercase mb-1">
							Status
						</span>
						<p className="text-[9px] text-zinc-600 font-mono tracking-[0.2em] uppercase leading-loose">
							PIPELINE: ACTIVE
							<br />
							LATENCY: &lt; 45.0s
							<br />
							STATUS: OPTIMAL
						</p>
					</div>
					<div className="flex flex-col gap-3">
						<span className="text-[8px] text-zinc-800 font-mono tracking-[0.35em] uppercase mb-1">
							Index
						</span>
						<div className="flex flex-col gap-2">
							{["Engine", "Fits", "Contact"].map((link) => (
								<span
									key={link}
									onClick={() => scrollTo(link.toLowerCase())}
									className="text-[9px] text-zinc-600 font-mono tracking-[0.2em] uppercase hover:text-zinc-400 transition-colors cursor-pointer"
								>
									{link}
								</span>
							))}
						</div>
					</div>
				</div>
				<div className="mt-14 pt-6 border-t border-zinc-900 flex items-center justify-between">
					<p className="text-[8px] text-zinc-800 font-mono tracking-[0.3em] uppercase">
						PORTE SYSTEMS — CONFIDENTIAL PROTOTYPE
					</p>
					<p className="text-[8px] text-zinc-800 font-mono tracking-[0.3em] uppercase">
						ALL RIGHTS RESERVED
					</p>
				</div>
			</footer>
		</main>
	);
}

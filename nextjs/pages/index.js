import { useState } from "react";
import Head from "next/head";
import Link from "next/link";

const categories = ["All shops", "Car care", "Hair salon", "Massage and spa"];

const shops = [
  {
    name: "Baan Suay Hair Studio",
    category: "Hair salon",
    area: "Soi Ari 4, Phaya Thai, Bangkok",
    summary: "3 services, from ฿450. Open Tue-Sun, 10:00-19:00.",
    services: [
      { name: "Hair spa treatment", price: 900 },
      { name: "Haircut and wash", price: 450 },
      { name: "Color consultation", price: 650 },
    ],
    deposit: "฿270",
  },
  {
    name: "Clean Ride Car Care",
    category: "Car care",
    area: "Lat Phrao 71, Wang Thonglang, Bangkok",
    summary: "3 services, from ฿300. Open Mon-Sat, 08:00-18:00.",
    services: [
      { name: "Interior detailing", price: 650 },
      { name: "Exterior wash", price: 300 },
      { name: "Full car care", price: 1600 },
    ],
    deposit: "฿150",
  },
  {
    name: "Mali Massage & Spa",
    category: "Massage and spa",
    area: "Ratchathewi, Bangkok",
    summary: "3 services, from ฿500. Open daily, 11:00-21:00.",
    services: [
      { name: "Thai massage", price: 500 },
      { name: "Aromatherapy massage", price: 850 },
      { name: "Foot reflexology", price: 700 },
    ],
    deposit: "฿200",
  },
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All shops");
  const [selectedShop, setSelectedShop] = useState(null);

  const visibleShops = shops.filter((shop) => {
    const matchesCategory = activeCategory === "All shops" || shop.category === activeCategory;
    const serviceNames = shop.services.map((service) => service.name).join(" ");
    const searchText = `${shop.name} ${shop.category} ${shop.area} ${serviceNames}`.toLowerCase();
    return matchesCategory && searchText.includes(query.trim().toLowerCase());
  });

  return (
    <>
      <Head>
        <title>Nadd | Find a local shop</title>
        <meta
          name="description"
          content="Find a local shop, explore services, and book your time with Nadd."
        />
      </Head>

      <main className="min-h-screen bg-[#0e1324] text-[#e8ecf8]">
        <header className="border-b border-[#26304b] bg-[#171e35]">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3 sm:px-8">
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight" aria-label="Nadd home">
                Nadd <span className="rounded bg-[#f2b93f] px-1.5 py-0.5 text-xs font-bold text-[#201a0c]">นัด</span>
              </Link>
              <a href="#shops" className="border-b-2 border-[#f2b93f] px-3 py-1.5 text-sm font-medium text-white">
                Find a shop
              </a>
            </div>
            <nav className="flex items-center gap-2" aria-label="Account navigation">
              <Link href="/login" className="rounded-md border border-[#35405d] px-3 py-1.5 text-sm font-medium hover:bg-[#202945]">
                Log in
              </Link>
              <Link href="/register" className="rounded-md bg-[#e8ecf8] px-3 py-1.5 text-sm font-semibold text-[#171e35] hover:bg-white">
                Sign up
              </Link>
            </nav>
          </div>
        </header>

        <section className="mx-auto grid max-w-5xl gap-8 px-5 pb-12 pt-10 sm:px-8 sm:pt-12 md:grid-cols-[1.18fr_0.82fr] md:items-center md:gap-12 md:pb-16">
          <div>
            <h1 className="max-w-xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl">
              Find a local shop and book your time.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-[#b7c2df]">
              Pick a service and a time, then pay a small deposit to hold it. You&apos;ll get a reminder on LINE before you go.
            </p>
            <label className="mt-5 block">
              <span className="sr-only">Search by shop, service or area</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by shop, service or area"
                className="h-[54px] w-full rounded-md border border-[#35405d] bg-[#171e35] px-3.5 text-sm text-[#e8ecf8] outline-none placeholder:text-[#7884a2] focus:border-[#f2b93f] focus:ring-1 focus:ring-[#f2b93f]"
              />
            </label>
            <div className="mt-3 flex flex-wrap gap-2" aria-label="Filter shops by category">
              {categories.map((category) => {
                const active = activeCategory === category;
                return (
                  <button
                    key={category}
                    type="button"
                    aria-pressed={active}
                    onClick={() => setActiveCategory(category)}
                    className={`rounded-full border px-3 py-2 text-xs font-medium transition-colors ${
                      active
                        ? "border-[#e8ecf8] bg-[#e8ecf8] text-[#171e35]"
                        : "border-[#35405d] bg-[#171e35] text-[#b7c2df] hover:border-[#7581a0] hover:text-white"
                    }`}
                  >
                    {category}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mx-auto w-full max-w-[390px] py-4 md:py-0">
            <div className="rotate-[-2deg] rounded-xl border border-[#303a58] bg-[#171e35] p-2 shadow-xl shadow-black/20">
              <div className="grid grid-cols-[108px_1fr] overflow-hidden rounded-lg">
                <div className="flex min-h-[126px] flex-col justify-center border-r-2 border-dashed border-[#0e1324] bg-[#f2b93f] px-4 text-[#1a1b20]">
                  <span className="text-3xl font-bold leading-none">13:00</span>
                  <span className="mt-2 text-sm font-medium">NEXT SLOT</span>
                  <span className="mt-3 text-[10px] font-semibold uppercase tracking-[0.12em]">Available</span>
                </div>
                <div className="flex flex-col justify-center px-4 py-3">
                  <span className="text-sm font-semibold text-white">Hair spa treatment</span>
                  <span className="mt-1 text-xs text-[#b7c2df]">Baan Suay Hair Studio</span>
                  <span className="mt-2 text-xs leading-5 text-[#b7c2df]">Hold it with a ฿270 deposit. Reminder the day before.</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="shops" className="mx-auto max-w-5xl px-5 pb-12 sm:px-8 sm:pb-16">
          <div className="flex items-baseline justify-between gap-4 border-b border-[#29334f] pb-3">
            <h2 className="text-lg font-semibold">
              {visibleShops.length} {visibleShops.length === 1 ? "shop" : "shops"} taking bookings
            </h2>
            <span className="text-xs text-[#8792ae]">Example shops</span>
          </div>

          {visibleShops.length > 0 ? (
            <div>
              {visibleShops.map((shop) => (
                <article key={shop.name} className="flex flex-col justify-between gap-4 border-b border-[#29334f] px-0 py-5 sm:flex-row sm:items-center sm:gap-8">
                  <div>
                    <h3 className="font-semibold text-[#e8ecf8]">{shop.name}</h3>
                    <p className="mt-1 text-sm text-[#aebbd9]">{shop.category}, {shop.area}</p>
                    <p className="mt-1 text-sm text-[#aebbd9]">{shop.summary}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedShop(shop)}
                    className="h-10 shrink-0 rounded-md border border-[#35405d] px-4 text-sm font-semibold hover:border-[#7581a0] hover:bg-[#171e35]"
                  >
                    View shop
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <p className="py-8 text-sm text-[#aebbd9]">No shops match that search. Try another shop, service, or area.</p>
          )}
        </section>

        {selectedShop && (
          <div
            className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) setSelectedShop(null);
            }}
          >
            <section role="dialog" aria-modal="true" aria-labelledby="shop-title" className="w-full max-w-lg border border-[#35405d] bg-[#171e35] p-6 shadow-2xl">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#f2b93f]">{selectedShop.category}</p>
                  <h2 id="shop-title" className="mt-2 text-xl font-semibold">{selectedShop.name}</h2>
                  <p className="mt-1 text-sm text-[#aebbd9]">{selectedShop.area}</p>
                </div>
                <button type="button" onClick={() => setSelectedShop(null)} className="rounded-md border border-[#35405d] px-3 py-1.5 text-sm hover:bg-[#202945]" aria-label="Close shop details">
                  Close
                </button>
              </div>
              <h3 className="mt-7 border-b border-[#35405d] pb-2 text-sm font-semibold">Services</h3>
              <ul className="divide-y divide-[#29334f]">
                {selectedShop.services.map((service) => (
                  <li key={service.name} className="flex items-center justify-between gap-4 py-3 text-sm">
                    <span>{service.name}</span>
                    <span className="shrink-0 text-[#aebbd9]">From ฿{service.price}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-xs leading-5 text-[#8792ae]">Example listing. Booking and payment will be available when the shop directory is connected.</p>
            </section>
          </div>
        )}
      </main>
    </>
  );
}
